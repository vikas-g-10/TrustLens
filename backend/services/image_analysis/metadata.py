"""
EXIF and Hardware Metadata Extraction for TrustLens Phase 4.

PRIVACY GUARANTEE:
Raw GPS coordinates (latitude, longitude, altitude) are NEVER exposed.
Only a boolean `gps_present: True` is reported.

EPISTEMIC GUARANTEE:
Missing EXIF metadata is strictly neutral. It provides zero evidence of manipulation
because many platforms (WhatsApp, Twitter/X, Telegram) automatically strip metadata.
Metadata completeness is classified transparently: 'present', 'partial', or 'unavailable'.
"""
from typing import Optional
from PIL import Image
from PIL.ExifTags import TAGS

from backend.schemas.image_analysis import ExifMetadata, MetadataStatus

EDITING_SOFTWARE_KEYWORDS = [
    "photoshop", "gimp", "lightroom", "canva", "snapseed",
    "pixelmator", "paint.net", "photopea", "affinity", "coreldraw"
]


def extract_exif_metadata(img: Image.Image) -> ExifMetadata:
    """
    Extract camera, hardware, and timestamp metadata from a decoded image.
    Enforces privacy by suppressing raw GPS coordinates.
    Enforces neutrality when EXIF is unavailable.
    Distinguishes metadata status: present, partial, or unavailable.
    """
    notes = []
    raw_exif = None

    try:
        raw_exif = img.getexif()
    except Exception:
        pass

    if not raw_exif or len(raw_exif) == 0:
        return ExifMetadata(
            available=False,
            metadata_status="unavailable",
            completeness_score=0.0,
            camera_make=None,
            camera_model=None,
            software=None,
            editing_software=None,
            timestamp=None,
            orientation=None,
            gps_present=False,
            color_space=None,
            raw_tags_count=0,
            notes=[
                "EXIF metadata unavailable (neutral): This provides ZERO positive or negative authenticity evidence.",
                "Social platforms and messaging apps routinely strip metadata to preserve privacy and bandwidth."
            ],
        )

    # Decode known tags
    camera_make: Optional[str] = None
    camera_model: Optional[str] = None
    software: Optional[str] = None
    editing_software: Optional[str] = None
    timestamp: Optional[str] = None
    orientation: Optional[int] = None
    color_space: Optional[str] = None
    gps_present = False
    raw_tags_count = len(raw_exif)

    for tag_id, value in raw_exif.items():
        tag_name = TAGS.get(tag_id, str(tag_id))

        if tag_name == "Make" and isinstance(value, str):
            camera_make = value.strip().replace("\x00", "")
        elif tag_name == "Model" and isinstance(value, str):
            camera_model = value.strip().replace("\x00", "")
        elif tag_name == "Software" and isinstance(value, str):
            software = value.strip().replace("\x00", "")
        elif tag_name in ("DateTime", "DateTimeOriginal", "DateTimeDigitized") and isinstance(value, str):
            if not timestamp:
                timestamp = value.strip().replace("\x00", "")
        elif tag_name == "Orientation" and isinstance(value, int):
            orientation = value
        elif tag_name == "ColorSpace":
            color_space = "sRGB" if value == 1 else f"Code {value}"
        elif tag_name == "GPSInfo":
            if value:
                gps_present = True

    # Check IFD sub-dictionaries if get_ifd is supported (PIL 9.2+)
    try:
        # Exif IFD (0x8769)
        exif_ifd = raw_exif.get_ifd(0x8769)
        if exif_ifd:
            raw_tags_count += len(exif_ifd)
            for tag_id, value in exif_ifd.items():
                tag_name = TAGS.get(tag_id, str(tag_id))
                if tag_name in ("DateTimeOriginal", "DateTimeDigitized") and not timestamp and isinstance(value, str):
                    timestamp = value.strip().replace("\x00", "")
                elif tag_name == "ColorSpace" and not color_space:
                    color_space = "sRGB" if value == 1 else f"Code {value}"

        # GPS IFD (0x8825)
        gps_ifd = raw_exif.get_ifd(0x8825)
        if gps_ifd and len(gps_ifd) > 0:
            gps_present = True
            raw_tags_count += len(gps_ifd)
    except Exception:
        pass

    # Check for known editing software in software string
    if software:
        soft_lower = software.lower()
        if any(kw in soft_lower for kw in EDITING_SOFTWARE_KEYWORDS):
            editing_software = software

    # Determine metadata completeness and status
    has_hardware = bool(camera_make or camera_model)
    has_timestamp = bool(timestamp)

    # Score completeness from 0.0 to 1.0
    completeness = 0.0
    if has_hardware:
        completeness += 0.35
    if has_timestamp:
        completeness += 0.35
    if software:
        completeness += 0.15
    if orientation is not None or color_space or gps_present:
        completeness += 0.15
    completeness = round(min(1.0, completeness), 2)

    if has_hardware and has_timestamp:
        status: MetadataStatus = "present"
    elif has_hardware or has_timestamp or raw_tags_count > 1:
        status = "partial"
    else:
        status = "unavailable"

    # Compile descriptive notes
    if camera_make or camera_model:
        dev = f"{camera_make or ''} {camera_model or ''}".strip()
        notes.append(f"Recorded capturing hardware: {dev}.")
    if editing_software:
        notes.append(f"Editing software signature detected: {editing_software}.")
    elif software:
        notes.append(f"Recorded processing software: {software}.")
    if timestamp:
        notes.append(f"Recorded capture timestamp: {timestamp}.")
    if gps_present:
        notes.append("Geographic location metadata is present in EXIF (coordinates withheld for privacy).")

    notes.append(
        f"Metadata status: {status} (completeness score: {completeness}). "
        "Metadata presence provides provenance context, but can be altered or injected."
    )

    return ExifMetadata(
        available=True,
        metadata_status=status,
        completeness_score=completeness,
        camera_make=camera_make,
        camera_model=camera_model,
        software=software,
        editing_software=editing_software,
        timestamp=timestamp,
        orientation=orientation,
        gps_present=gps_present,
        color_space=color_space,
        raw_tags_count=raw_tags_count,
        notes=notes,
    )
