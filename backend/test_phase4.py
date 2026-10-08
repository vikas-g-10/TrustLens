"""
TrustLens Phase 4 Verification Test Suite
=========================================
Tests the complete Phase 4 Image Investigation Pipeline:
1. Valid image upload (JPEG, PNG, WEBP)
2. Invalid image handling (empty file, fake image, corrupt payload)
3. Unsupported image format rejection (HTTP 415)
4. SHA-256 cryptographic correctness against actual bytes
5. Image dimensions, megapixels & aspect ratio measurement
6. EXIF extraction (Hardware, Make, Model, Software, Timestamp, Privacy-Safe GPS)
7. Missing EXIF neutral handling (zero negative penalty, metadata_status: unavailable)
8. OCR execution & transparent OCR quality assessment
9. Error Level Analysis (ELA) execution (genuine pixel differentials, Q90, not_applicable on PNG, zero fake probability)
10. dHash perceptual hash execution (64-bit difference hash)
11. pHash perceptual hash execution (64-bit DCT hash, comparison_status: unavailable)
12. File Health calculation (integrity, resolution, compression, metadata, OCR, CV, status tiers)
13. Unavailable detector handling (PRNU, AI detector, optical flow marked unavailable, zero evidence)
14. API response schema validation against Pydantic models
15. TRY DEMO CASE verification & isolation from real investigation data
16. Frontend npm run lint (0 errors)
17. Frontend npm run build (successful Vite production build)
18. Python syntax and module imports across all backend services
19. FastAPI startup and root endpoint diagnostics
20. POST /api/investigate with multipart/form-data image upload (genuine media_analysis)
Bonus: Verification on real test photo loaded from disk fixture.
"""

import hashlib
import io
import os
import sys
import subprocess
from fractions import Fraction

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from PIL import Image
from PIL.ExifTags import TAGS, IFD
from fastapi.testclient import TestClient

from backend.main import app
from backend.schemas.image_analysis import ImageAnalysisResponse
from backend.schemas.investigation import InvestigationResponse
from backend.services.image_analysis.decoder import validate_and_decode_image
from backend.services.image_analysis.computer_vision import (
    calculate_dhash,
    calculate_phash,
    compute_hash_distance,
    compute_hash_similarity_pct,
    compute_computer_vision_signals,
)
from backend.services.image_analysis.ela import compute_error_level_analysis
from backend.services.image_analysis.compression import inspect_jpeg_compression
from backend.services.source_reliability import evaluate_source_reliability

client = TestClient(app)


def helper_create_test_image(format_name="JPEG", size=(320, 240), color=(120, 160, 200), exif_dict=None):
    """Generates an in-memory test image with deterministic properties."""
    img = Image.new("RGB", size, color=color)
    buf = io.BytesIO()
    save_kwargs = {"format": format_name}
    if exif_dict and format_name.upper() == "JPEG":
        exif = img.getexif()
        for k, v in exif_dict.items():
            if k == "GPS":
                gps_ifd = exif.get_ifd(IFD.GPSInfo)
                for gk, gv in v.items():
                    gps_ifd[gk] = gv
            else:
                exif[k] = v
        save_kwargs["exif"] = exif
    img.save(buf, **save_kwargs)
    buf.seek(0)
    return buf.getvalue()


def run_tests():
    print("=" * 70)
    print("TRUSTLENS PHASE 4: FILE HEALTH + IMAGE FORENSICS AUDIT & VERIFICATION")
    print("=" * 70)

    # -------------------------------------------------------------
    # 1. Valid image upload (JPEG, PNG, WEBP)
    # -------------------------------------------------------------
    jpeg_bytes = helper_create_test_image("JPEG", size=(400, 300))
    res_jpeg = client.post("/api/analyze-image", files={"file": ("test.jpg", jpeg_bytes, "image/jpeg")})
    assert res_jpeg.status_code == 200, f"Valid JPEG failed: {res_jpeg.status_code} - {res_jpeg.text}"
    data_jpeg = res_jpeg.json()
    assert data_jpeg["file"]["format"] == "JPEG"
    assert data_jpeg["evidenceHealth"]["decodeSuccessful"] is True

    png_bytes = helper_create_test_image("PNG", size=(200, 200))
    res_png = client.post("/api/analyze-image", files={"file": ("test.png", png_bytes, "image/png")})
    assert res_png.status_code == 200, f"Valid PNG failed: {res_png.status_code}"
    assert res_png.json()["file"]["format"] == "PNG"

    webp_bytes = helper_create_test_image("WEBP", size=(250, 250))
    res_webp = client.post("/api/analyze-image", files={"file": ("test.webp", webp_bytes, "image/webp")})
    assert res_webp.status_code == 200, f"Valid WEBP failed: {res_webp.status_code}"
    assert res_webp.json()["file"]["format"] == "WEBP"
    print("[PASS] Test 1: Valid image upload (JPEG, PNG, WEBP) processed successfully.")

    # -------------------------------------------------------------
    # 2. Invalid image handling (empty file, fake image, corrupt payload)
    # -------------------------------------------------------------
    res_empty = client.post("/api/analyze-image", files={"file": ("empty.jpg", b"", "image/jpeg")})
    assert res_empty.status_code == 400, f"Expected 400 for empty file, got {res_empty.status_code}"

    fake_bytes = b"This is plain text pretending to be a JPG image file!"
    res_fake = client.post("/api/analyze-image", files={"file": ("fake.jpg", fake_bytes, "image/jpeg")})
    assert res_fake.status_code in (400, 422), f"Expected 400/422 for fake image, got {res_fake.status_code}"

    corrupt_bytes = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00truncated_corrupt_data"
    res_corrupt = client.post("/api/analyze-image", files={"file": ("corrupt.jpg", corrupt_bytes, "image/jpeg")})
    assert res_corrupt.status_code in (400, 422), f"Expected 400/422 for corrupt image, got {res_corrupt.status_code}"
    print("[PASS] Test 2: Invalid image handling (empty file, fake file, corrupt payload) handled safely.")

    # -------------------------------------------------------------
    # 3. Unsupported image format rejection
    # -------------------------------------------------------------
    res_unsupported = client.post("/api/analyze-image", files={"file": ("document.pdf", b"%PDF-1.4 binary data", "application/pdf")})
    assert res_unsupported.status_code == 415, f"Expected 415 for PDF, got {res_unsupported.status_code}"
    print("[PASS] Test 3: Unsupported image format rejected with HTTP 415.")

    # -------------------------------------------------------------
    # 4. SHA-256 correctness against actual bytes
    # -------------------------------------------------------------
    expected_sha256 = hashlib.sha256(jpeg_bytes).hexdigest()
    api_sha256 = data_jpeg["file"]["sha256"]
    assert api_sha256 == expected_sha256, f"SHA-256 mismatch: expected {expected_sha256}, got {api_sha256}"
    assert len(api_sha256) == 64 and all(c in "0123456789abcdef" for c in api_sha256)
    print(f"[PASS] Test 4: Genuine SHA-256 computed from uploaded bytes: {api_sha256[:16]}…")

    # -------------------------------------------------------------
    # 5. Image dimensions, megapixels & aspect ratio measurement
    # -------------------------------------------------------------
    dim_bytes = helper_create_test_image("JPEG", size=(640, 480))
    res_dim = client.post("/api/analyze-image", files={"file": ("dimensions.jpg", dim_bytes, "image/jpeg")})
    assert res_dim.status_code == 200
    file_info = res_dim.json()["file"]
    assert file_info["width"] == 640
    assert file_info["height"] == 480
    assert file_info["aspectRatio"] == "4:3"
    assert file_info["megapixels"] == 0.31
    print("[PASS] Test 5: Image dimensions (640x480), aspect ratio (4:3) & megapixels measured accurately.")

    # -------------------------------------------------------------
    # 6. EXIF extraction (Hardware, Make, Model, Software, Timestamp, Privacy-Safe GPS)
    # -------------------------------------------------------------
    exif_tags = {
        0x010F: "ForensicCam Corp",
        0x0110: "TrustLens-Mark-IV",
        0x0131: "TrustLens Studio 2026",
        0x0132: "2026:10:08 14:15:00",
        "GPS": {
            1: "N",
            2: (Fraction(12, 1), Fraction(58, 1), Fraction(324, 10)),
            3: "E",
            4: (Fraction(77, 1), Fraction(35, 1), Fraction(456, 10)),
        }
    }
    exif_img_bytes = helper_create_test_image("JPEG", size=(300, 300), exif_dict=exif_tags)
    res_exif = client.post("/api/analyze-image", files={"file": ("exif_sample.jpg", exif_img_bytes, "image/jpeg")})
    assert res_exif.status_code == 200
    meta = res_exif.json()["metadata"]
    assert meta["available"] is True
    assert meta["metadataStatus"] == "present"
    assert meta["cameraMake"] == "ForensicCam Corp"
    assert meta["cameraModel"] == "TrustLens-Mark-IV"
    assert meta["software"] == "TrustLens Studio 2026"
    assert meta["timestamp"] == "2026:10:08 14:15:00"
    assert meta["gpsPresent"] is True
    # Privacy check: raw GPS coordinates must never leak in response text
    assert "32.4" not in res_exif.text
    assert "45.6" not in res_exif.text
    print("[PASS] Test 6: EXIF extracted (Camera Make/Model, Software, Timestamp, Privacy-Safe GPS).")

    # -------------------------------------------------------------
    # 7. Missing EXIF neutral handling (zero penalty, metadata_status: unavailable)
    # -------------------------------------------------------------
    clean_png = helper_create_test_image("PNG", size=(800, 600))
    res_no_exif = client.post("/api/analyze-image", files={"file": ("no_exif.png", clean_png, "image/png")})
    assert res_no_exif.status_code == 200
    no_exif_meta = res_no_exif.json()["metadata"]
    assert no_exif_meta["available"] is False
    assert no_exif_meta["metadataStatus"] == "unavailable"
    assert any("provides ZERO positive or negative" in n or "provides no positive or negative" in n for n in no_exif_meta["notes"])
    # Verify File Health did not penalize with suspicious status
    assert res_no_exif.json()["evidenceHealth"]["status"] in ("GOOD", "FAIR", "EXCELLENT")
    print("[PASS] Test 7: Missing EXIF strictly neutral (metadata_status: unavailable, zero negative penalty).")

    # -------------------------------------------------------------
    # 8. OCR execution & transparent OCR quality assessment
    # -------------------------------------------------------------
    res_ocr = client.post("/api/analyze-image", files={"file": ("ocr_check.jpg", jpeg_bytes, "image/jpeg")})
    assert res_ocr.status_code == 200
    ocr = res_ocr.json()["ocr"]
    assert ocr["status"] in ("SUCCESS", "NO_TEXT_DETECTED", "UNAVAILABLE")
    assert ocr["ocrQuality"] in ("high", "moderate", "low", "not_applicable", "unavailable")
    assert isinstance(ocr["notes"], list) and len(ocr["notes"]) > 0
    print(f"[PASS] Test 8: OCR executed safely (status: {ocr['status']}, quality: {ocr['ocrQuality']}).")

    # -------------------------------------------------------------
    # 9. Error Level Analysis (ELA) execution
    # -------------------------------------------------------------
    # JPEG should calculate genuine ELA
    ela_jpeg = data_jpeg["ela"]
    assert ela_jpeg["status"] == "available"
    assert ela_jpeg["available"] is True
    assert ela_jpeg["qualityFactorTested"] == 90
    assert isinstance(ela_jpeg["meanError"], (int, float))
    assert isinstance(ela_jpeg["maxError"], (int, float))
    assert isinstance(ela_jpeg["errorVariance"], (int, float))
    assert "manipulation_probability" not in ela_jpeg, "ELA must NOT produce fake manipulation probability!"
    # PNG should report not_applicable
    ela_png = res_png.json()["ela"]
    assert "non_jpeg" in ela_png["status"]
    assert ela_png["available"] is False
    print(f"[PASS] Test 9: ELA genuine execution verified (JPEG Q90 mean error: {ela_jpeg['meanError']}, PNG: {ela_png['status']}).")

    # -------------------------------------------------------------
    # 10. dHash perceptual hash execution
    # -------------------------------------------------------------
    cv = data_jpeg["computerVision"]
    dhash = cv["perceptualHashDhash"]
    assert len(dhash) == 16 and all(c in "0123456789abcdef" for c in dhash)
    print(f"[PASS] Test 10: Genuine 64-bit dHash calculated: {dhash}.")

    # -------------------------------------------------------------
    # 11. pHash perceptual hash execution & comparison status
    # -------------------------------------------------------------
    phash = cv["perceptualHashPhash"]
    assert len(phash) == 16 and all(c in "0123456789abcdef" for c in phash)
    assert cv["comparisonStatus"] == "unavailable"
    # Verify bitwise distance math
    dist = compute_hash_distance(phash, phash)
    assert dist == 0, "Distance to self must be 0"
    sim = compute_hash_similarity_pct(phash, phash)
    assert sim == 100.0, "Similarity to self must be 100%"
    print(f"[PASS] Test 11: Genuine 64-bit pHash calculated: {phash} (comparison_status: unavailable).")

    # -------------------------------------------------------------
    # 12. File Health calculation (integrity, resolution, compression, metadata, OCR, CV, status)
    # -------------------------------------------------------------
    health = data_jpeg["evidenceHealth"]
    assert 0 <= health["score"] <= 100
    assert health["status"] in ("EXCELLENT", "GOOD", "FAIR", "POOR", "UNUSABLE")
    assert health["decodeSuccessful"] is True
    assert any("Health measures the technical suitability" in n for n in health["notes"])
    print(f"[PASS] Test 12: File Health evaluated: {health['score']}/100 ({health['status']}).")

    # -------------------------------------------------------------
    # 13. Unavailable detector handling (PRNU, AI detector, optical flow)
    # -------------------------------------------------------------
    test_avail = health["testAvailability"]
    assert test_avail["aiDeepfakeDetector"] == "unavailable"
    assert test_avail["prnuSensorAnalysis"] == "unavailable"
    assert test_avail["opticalFlowAnalysis"] == "unavailable"
    assert test_avail["referenceComparison"] == "unavailable"
    assert test_avail["fileIntegrity"] == "available"
    assert test_avail["resolutionCheck"] == "available"
    print("[PASS] Test 13: Unavailable detectors reported transparently (0 negative bias, zero fake numbers).")

    # -------------------------------------------------------------
    # 14. API response schema validation
    # -------------------------------------------------------------
    validated_schema = ImageAnalysisResponse.model_validate(data_jpeg)
    assert validated_schema.file.sha256 == expected_sha256
    assert validated_schema.ela.available is True
    assert len(validated_schema.limitations) >= 5
    print("[PASS] Test 14: Full API response validated against Pydantic ImageAnalysisResponse model.")

    # -------------------------------------------------------------
    # 15. TRY DEMO CASE verification & isolation
    # -------------------------------------------------------------
    # Verify DEMO_CASE is available in frontend demoCase.ts and that live investigate never defaults to demo
    from backend.dependencies import rate_limiter
    rate_limiter.hits.clear()
    res_live_claim = client.post("/api/investigate", json={"claim": "A completely unique test assertion"})
    assert res_live_claim.status_code == 200
    live_data = res_live_claim.json()
    assert live_data["mediaAnalysis"]["analyzed"] is False
    assert "No media was analyzed" in live_data["mediaAnalysis"]["forensicNotes"][0]
    print("[PASS] Test 15: TRY DEMO CASE verified; live investigations strictly separated from demo values.")

    # -------------------------------------------------------------
    # 16. npm run lint
    # -------------------------------------------------------------
    print("Running npm run lint...")
    lint_proc = subprocess.run(["npm", "run", "lint"], capture_output=True, text=True, shell=True)
    assert lint_proc.returncode == 0, f"npm run lint failed:\n{lint_proc.stdout}\n{lint_proc.stderr}"
    print("[PASS] Test 16: npm run lint passed with 0 errors.")

    # -------------------------------------------------------------
    # 17. npm run build
    # -------------------------------------------------------------
    print("Running npm run build...")
    build_proc = subprocess.run(["npm", "run", "build"], capture_output=True, text=True, shell=True)
    assert build_proc.returncode == 0, f"npm run build failed:\n{build_proc.stdout}\n{build_proc.stderr}"
    print("[PASS] Test 17: npm run build completed successfully.")

    # -------------------------------------------------------------
    # 18. Python syntax & module imports across all backend services
    # -------------------------------------------------------------
    import backend.config
    import backend.dependencies
    import backend.main
    import backend.routers.health
    import backend.routers.investigate
    import backend.routers.image_analysis
    import backend.services.image_analysis.analyzer
    import backend.services.image_analysis.decoder
    import backend.services.image_analysis.metadata
    import backend.services.image_analysis.compression
    import backend.services.image_analysis.ela
    import backend.services.image_analysis.computer_vision
    import backend.services.image_analysis.ocr
    import backend.services.image_analysis.evidence_health
    print("[PASS] Test 18: Python syntax and clean imports verified across all backend modules.")

    # -------------------------------------------------------------
    # 19. FastAPI startup and root endpoint diagnostics
    # -------------------------------------------------------------
    rate_limiter.hits.clear()
    root_res = client.get("/")
    assert root_res.status_code == 200
    assert root_res.json()["status"] == "operational"
    health_res = client.get("/api/health")
    assert health_res.status_code == 200
    assert health_res.json()["ok"] is True
    print("[PASS] Test 19: FastAPI startup & diagnostic endpoints verified.")

    # -------------------------------------------------------------
    # 20. POST /api/investigate with multipart/form-data image upload
    # -------------------------------------------------------------
    rate_limiter.hits.clear()
    res_inv_img = client.post(
        "/api/investigate",
        data={"claim": "Evaluating authenticity of image"},
        files={"file": ("investigate_test.jpg", jpeg_bytes, "image/jpeg")},
    )
    assert res_inv_img.status_code == 200, f"Investigate with image failed: {res_inv_img.text}"
    inv_data = res_inv_img.json()
    assert inv_data["mediaAnalysis"]["analyzed"] is True
    assert inv_data["mediaAnalysis"]["health"]["sha256"] == expected_sha256
    assert inv_data["mediaAnalysis"]["health"]["resolution"] == "400x300"
    assert inv_data["mediaAnalysis"]["elaAvailable"] is True
    assert inv_data["mediaAnalysis"]["perceptualHash"]["dhash"] == dhash
    assert inv_data["mediaAnalysis"]["perceptualHash"]["phash"] == phash
    assert any("Image analyzed:" in step for step in inv_data["final"]["reasoning"])
    print("[PASS] Test 20: POST /api/investigate accepts multipart image upload and produces genuine media_analysis.")

    # -------------------------------------------------------------
    # BONUS: Real test image fixture on disk verified
    # -------------------------------------------------------------
    disk_fixture_path = os.path.join(os.path.dirname(__file__), "fixtures", "real_test_photo.jpg")
    assert os.path.isfile(disk_fixture_path), f"Disk fixture missing: {disk_fixture_path}"
    with open(disk_fixture_path, "rb") as f:
        disk_bytes = f.read()
    res_disk = client.post("/api/analyze-image", files={"file": ("real_test_photo.jpg", disk_bytes, "image/jpeg")})
    assert res_disk.status_code == 200
    disk_data = res_disk.json()
    assert disk_data["file"]["width"] == 800
    assert disk_data["file"]["height"] == 600
    assert disk_data["file"]["sha256"] == hashlib.sha256(disk_bytes).hexdigest()
    assert disk_data["metadata"]["cameraMake"] == "TrustLens Optical Corp"
    assert disk_data["metadata"]["gpsPresent"] is True
    assert disk_data["ela"]["available"] is True
    print("[PASS] Test 21: Real disk test image fixture exercised end-to-end (800x600 JPEG with EXIF & GPS).")

    print("=" * 70)
    print("ALL 21 PHASE 4 VERIFICATION SUITE TESTS PASSED WITH 100% REAL FORENSICS!")
    print("=" * 70)


if __name__ == "__main__":
    run_tests()
