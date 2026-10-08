"""
Computer Vision Signals and Perceptual Hashing for TrustLens Phase 4.

Calculates real, explainable image quality and visual metrics:
1. Sharpness via discrete 2D Laplacian variance.
2. Brightness via luminance mean and exposure tiering.
3. Contrast via root-mean-square (RMS) luminance standard deviation.
4. Edge density via spatial gradient thresholding.
5. High-frequency noise variance.
6. Real deterministic perceptual hashes (dHash and pHash).
"""
import math
import numpy as np
from PIL import Image

from backend.schemas.image_analysis import ComputerVisionSignals, SharpnessLevel, BrightnessLevel


def _compute_dhash(img: Image.Image) -> str:
    """
    Compute Difference Hash (dHash).
    Resizes to 9x8 grayscale, evaluates horizontal gradient direction across 64 bits.
    """
    resized = img.convert("L").resize((9, 8), Image.Resampling.LANCZOS)
    arr = np.array(resized, dtype=np.float64)
    diff = arr[:, 1:] > arr[:, :-1]  # 8x8 booleans
    packed = np.packbits(diff.flatten())
    return "".join(f"{b:02x}" for b in packed)


def _compute_phash(img: Image.Image) -> str:
    """
    Compute Perceptual Hash (pHash) via Discrete Cosine Transform (DCT).
    Resizes to 32x32 grayscale, computes 2D DCT, extracts 8x8 low-frequency AC components,
    and thresholds against median.
    """
    N = 32
    resized = img.convert("L").resize((N, N), Image.Resampling.LANCZOS)
    arr = np.array(resized, dtype=np.float64)

    # Construct 1D DCT matrix C
    x = np.arange(N)
    u = np.arange(N).reshape(-1, 1)
    C = np.sqrt(2.0 / N) * np.cos(((2.0 * x + 1.0) * u * np.pi) / (2.0 * N))
    C[0, :] = 1.0 / np.sqrt(N)

    # 2D DCT: C * arr * C^T
    dct = C @ arr @ C.T

    # Extract top-left 8x8 frequency block
    block = dct[0:8, 0:8]
    # Median of AC components (exclude DC component at [0, 0])
    ac_vals = block.flatten()[1:]
    med = float(np.median(ac_vals)) if len(ac_vals) > 0 else float(np.mean(block))

    bits = block > med
    packed = np.packbits(bits.flatten())
    return "".join(f"{b:02x}" for b in packed)


def extract_computer_vision_signals(img: Image.Image) -> ComputerVisionSignals:
    """
    Compute deterministic CV signals and perceptual hashes.
    """
    # 1. Grayscale luminance array
    gray_img = img.convert("L")
    gray = np.array(gray_img, dtype=np.float64)
    h, w = gray.shape

    # 2. Brightness & Contrast
    brightness_mean = float(np.mean(gray))
    contrast_rms = float(np.std(gray))

    if brightness_mean < 45.0:
        brightness_assessment: BrightnessLevel = "underexposed"
    elif brightness_mean > 215.0:
        brightness_assessment: BrightnessLevel = "overexposed"
    else:
        brightness_assessment: BrightnessLevel = "normal"

    # 3. Sharpness via 2D Laplacian operator
    if h >= 3 and w >= 3:
        # Standard discrete Laplacian convolution [[0, 1, 0], [1, -4, 1], [0, 1, 0]]
        laplacian = (
            gray[:-2, 1:-1]
            + gray[2:, 1:-1]
            + gray[1:-1, :-2]
            + gray[1:-1, 2:]
            - 4.0 * gray[1:-1, 1:-1]
        )
        sharpness_score = float(np.var(laplacian))
    else:
        sharpness_score = 0.0

    if sharpness_score < 40.0:
        sharpness_assessment: SharpnessLevel = "blur_detected"
    elif sharpness_score < 120.0:
        sharpness_assessment: SharpnessLevel = "low"
    elif sharpness_score < 450.0:
        sharpness_assessment: SharpnessLevel = "moderate"
    else:
        sharpness_assessment: SharpnessLevel = "high"

    # 4. Edge density via spatial gradient
    if h >= 3 and w >= 3:
        gx = gray[1:-1, 2:] - gray[1:-1, :-2]
        gy = gray[2:, 1:-1] - gray[:-2, 1:-1]
        grad_mag = np.sqrt(gx**2 + gy**2)
        edge_count = np.sum(grad_mag > 30.0)
        edge_density = float(edge_count / grad_mag.size)
    else:
        edge_density = 0.0

    # 5. Noise variance via high-frequency residual
    if h >= 3 and w >= 3:
        box_smooth = (
            gray[:-2, :-2] + gray[:-2, 1:-1] + gray[:-2, 2:]
            + gray[1:-1, :-2] + gray[1:-1, 1:-1] + gray[1:-1, 2:]
            + gray[2:, :-2] + gray[2:, 1:-1] + gray[2:, 2:]
        ) / 9.0
        residual = gray[1:-1, 1:-1] - box_smooth
        noise_variance = float(np.var(residual))
    else:
        noise_variance = 0.0

    # 6. Perceptual Hashes
    dhash = _compute_dhash(img)
    phash = _compute_phash(img)

    return ComputerVisionSignals(
        sharpness_score=round(sharpness_score, 2),
        sharpness_assessment=sharpness_assessment,
        brightness_mean=round(brightness_mean, 2),
        brightness_assessment=brightness_assessment,
        contrast_rms=round(contrast_rms, 2),
        edge_density=round(edge_density, 4),
        perceptual_hash_dhash=dhash,
        perceptual_hash_phash=phash,
        comparison_status="unavailable",
        noise_variance=round(noise_variance, 2),
    )


def compute_hash_distance(hash1: str, hash2: str) -> int:
    """Compute bitwise Hamming distance between two 64-bit hex hashes."""
    if not hash1 or not hash2 or len(hash1) != len(hash2):
        return 64
    try:
        v1 = int(hash1, 16)
        v2 = int(hash2, 16)
        return bin(v1 ^ v2).count("1")
    except ValueError:
        return 64


def compute_hash_similarity_pct(hash1: str, hash2: str) -> float:
    """Compute similarity percentage (0-100) between two 64-bit hex hashes."""
    dist = compute_hash_distance(hash1, hash2)
    return round(max(0.0, (1.0 - dist / 64.0) * 100.0), 1)


# Public helper aliases
calculate_dhash = _compute_dhash
calculate_phash = _compute_phash
compute_computer_vision_signals = extract_computer_vision_signals

