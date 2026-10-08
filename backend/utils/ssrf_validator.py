import ipaddress
import socket
from urllib.parse import ParseResult
from typing import List, Set

# Standard web ports permitted
ALLOWED_PORTS: Set[int] = {80, 443}

# Blocked subnets matching server/urlAnalysis.ts
BLOCKED_IPV4_SUBNETS = [
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("100.64.0.0/10"),     # Carrier-grade NAT
    ipaddress.ip_network("127.0.0.0/8"),      # Loopback
    ipaddress.ip_network("169.254.0.0/16"),   # Link-local / Cloud metadata (169.254.169.254)
    ipaddress.ip_network("172.16.0.0/12"),    # Private IPv4
    ipaddress.ip_network("192.0.0.0/24"),     # IETF Protocol Assignments
    ipaddress.ip_network("192.0.2.0/24"),     # TEST-NET-1
    ipaddress.ip_network("192.168.0.0/16"),   # Private IPv4
    ipaddress.ip_network("198.18.0.0/15"),    # Benchmarking
    ipaddress.ip_network("198.51.100.0/24"),  # TEST-NET-2
    ipaddress.ip_network("203.0.113.0/24"),   # TEST-NET-3
    ipaddress.ip_network("224.0.0.0/4"),      # Multicast
    ipaddress.ip_network("240.0.0.0/4"),      # Reserved
]

BLOCKED_IPV6_SUBNETS = [
    ipaddress.ip_network("::/128"),
    ipaddress.ip_network("::1/128"),          # Loopback
    ipaddress.ip_network("fc00::/7"),         # Unique local address (private)
    ipaddress.ip_network("fe80::/10"),        # Link-local
    ipaddress.ip_network("ff00::/8"),         # Multicast
    ipaddress.ip_network("64:ff9b::/96"),     # IPv4-IPv6 translation
    ipaddress.ip_network("2001:db8::/32"),    # Documentation
    ipaddress.ip_network("2002::/16"),        # 6to4
    ipaddress.ip_network("100::/64"),         # Discard-only
]

BLOCKED_HOSTNAME_SUFFIXES = (
    ".localhost",
    ".local",
    ".internal",
    ".lan",
    ".home.arpa",
)


class SSRFValidationError(Exception):
    """Raised when a URL or hostname violates SSRF protections."""
    def __init__(self, code: str, message: str, status_code: int = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


def is_blocked_ip(ip_str: str) -> bool:
    """
    Check if an IPv4 or IPv6 address is in a private, loopback,
    link-local, cloud metadata, or reserved range.
    """
    try:
        # Strip IPv6 scope if present
        clean_ip = ip_str.split("%")[0].strip("[]")
        ip = ipaddress.ip_address(clean_ip)

        # Handle IPv4-mapped IPv6 addresses (::ffff:192.0.2.1)
        if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
            ip = ip.ipv4_mapped

        # Universal standard checks
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved or ip.is_unspecified:
            return True

        if isinstance(ip, ipaddress.IPv4Address):
            for subnet in BLOCKED_IPV4_SUBNETS:
                if ip in subnet:
                    return True
        elif isinstance(ip, ipaddress.IPv6Address):
            for subnet in BLOCKED_IPV6_SUBNETS:
                if ip in subnet:
                    return True

        return False
    except ValueError:
        # Invalid IP string: fail-closed for safety
        return True


def assert_safe_hostname(host: str) -> None:
    """Check hostname against prohibited internal, single-label, and cloud metadata targets."""
    clean_host = host.strip("[]").lower()
    if not clean_host:
        raise SSRFValidationError("INVALID_URL", "Hostname is empty.")

    if clean_host == "localhost" or any(clean_host.endswith(s) for s in BLOCKED_HOSTNAME_SUFFIXES):
        raise SSRFValidationError("BLOCKED_HOST", "Localhost and internal hostnames are not allowed.")

    if clean_host == "metadata.google.internal":
        raise SSRFValidationError("BLOCKED_HOST", "Cloud metadata endpoints are strictly blocked.")

    # Check if host is direct IP literal
    try:
        ipaddress.ip_address(clean_host)
        is_ip_literal = True
    except ValueError:
        is_ip_literal = False

    if is_ip_literal:
        if is_blocked_ip(clean_host):
            raise SSRFValidationError("BLOCKED_HOST", "Private, loopback and reserved IP addresses are not allowed.")
        return  # Valid public IP literal

    # Reject single-label hostnames (e.g. 'router', 'corp', 'internal')
    if "." not in clean_host:
        raise SSRFValidationError("BLOCKED_HOST", "Single-label hostnames are not allowed.")


def validate_url_scheme_and_port(parsed: ParseResult) -> int:
    """Verify protocol scheme and port number."""
    scheme = (parsed.scheme or "").lower()
    if scheme not in ("http", "https"):
        raise SSRFValidationError("INVALID_URL", "Only http:// and https:// URLs are supported.")

    if parsed.username or parsed.password:
        raise SSRFValidationError("INVALID_URL", "URLs with embedded credentials are not accepted.")

    port = parsed.port
    if port is None:
        port = 443 if scheme == "https" else 80

    if port not in ALLOWED_PORTS:
        raise SSRFValidationError("BLOCKED_HOST", "Only standard web ports (80/443) are allowed.")

    return port


def resolve_and_verify_destination(host: str, port: int) -> List[str]:
    """
    DNS lookup resolving hostname and verifying that ALL resolved IP addresses
    are non-private and public. Prevents DNS rebinding and internal subnet access.
    """
    clean_host = host.strip("[]")
    
    # Check if host is already an IP address
    try:
        ip = ipaddress.ip_address(clean_host)
        if is_blocked_ip(clean_host):
            raise SSRFValidationError("BLOCKED_HOST", "Host resolves to a private or internal address.")
        return [clean_host]
    except ValueError:
        pass

    try:
        addr_info = socket.getaddrinfo(clean_host, port, family=socket.AF_UNSPEC, type=socket.SOCK_STREAM)
    except (socket.gaierror, socket.herror) as e:
        raise SSRFValidationError("DNS_FAILURE", "The domain name could not be resolved (it may not exist).")
    except Exception as e:
        raise SSRFValidationError("DNS_FAILURE", f"DNS resolution failed: {str(e)}")

    if not addr_info:
        raise SSRFValidationError("DNS_FAILURE", "No address information returned for host.")

    verified_ips = []
    for family, _, _, _, sockaddr in addr_info:
        ip_addr = sockaddr[0]
        if is_blocked_ip(ip_addr):
            raise SSRFValidationError("BLOCKED_HOST", "The host resolves to a private or internal address and was blocked.")
        if ip_addr not in verified_ips:
            verified_ips.append(ip_addr)

    if not verified_ips:
        raise SSRFValidationError("BLOCKED_HOST", "Host resolves to no usable public addresses.")

    return verified_ips


def validate_url_ssrf_safety(url_str: str):
    """
    Convenience validator returning (is_safe, error_code, error_message).
    Validates URL parsing, scheme, port, hostname, and DNS resolution.
    """
    from urllib.parse import urlparse
    try:
        parsed = urlparse(url_str)
        if not parsed.hostname:
            return False, "INVALID_URL", "URL does not contain a valid host."
        port = validate_url_scheme_and_port(parsed)
        assert_safe_hostname(parsed.hostname)
        resolve_and_verify_destination(parsed.hostname, port)
        return True, None, None
    except SSRFValidationError as e:
        return False, e.code, e.message
    except Exception as e:
        return False, "INVALID_URL", str(e)

