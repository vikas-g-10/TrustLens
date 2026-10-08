"""
Automated validation script for TrustLens Phase 1 FastAPI implementation.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from backend.main import app

def test_phase1():
    client = TestClient(app)
    
    # 1. Root check
    res_root = client.get("/")
    assert res_root.status_code == 200, f"Root returned {res_root.status_code}"
    print("[PASS] GET / -> status 200")
    
    # 2. Health check
    res_health = client.get("/api/health")
    assert res_health.status_code == 200, f"Health returned {res_health.status_code}"
    health_data = res_health.json()
    assert health_data.get("ok") is True
    assert "groqConfigured" in health_data
    assert "model" in health_data
    print("[PASS] GET /api/health -> status 200, payload:", health_data)
    
    # 3. Investigate endpoint (valid claim)
    sample_claim = "Electric vehicles produce zero lifetime carbon emissions."
    res_inv = client.post("/api/investigate", json={"claim": sample_claim, "url": "https://example.com/ev-facts"})
    assert res_inv.status_code == 200, f"Investigate returned {res_inv.status_code}: {res_inv.text}"
    inv_data = res_inv.json()
    
    # Contract validation with React frontend expectations
    assert "claim" in inv_data, "Missing 'claim'"
    assert "final" in inv_data, "Missing 'final' block expected by investigationApi.ts"
    assert "verdict" in inv_data["final"], "Missing 'verdict' in final"
    assert "confidence" in inv_data["final"], "Missing 'confidence' in final"
    assert "summary" in inv_data["final"], "Missing 'summary' in final"
    assert "supportingEvidence" in inv_data["final"], "Missing camelCase 'supportingEvidence'"
    assert "contradictingEvidence" in inv_data["final"], "Missing camelCase 'contradictingEvidence'"
    assert "uncertainties" in inv_data["final"], "Missing 'uncertainties'"
    assert "reasoning" in inv_data["final"], "Missing 'reasoning'"
    assert "aiAvailable" in inv_data, "Missing camelCase 'aiAvailable'"
    assert "generatedAt" in inv_data, "Missing camelCase 'generatedAt'"
    
    print("[PASS] POST /api/investigate -> status 200, contract verified:", {
        "claim": inv_data["claim"],
        "verdict": inv_data["final"]["verdict"],
        "confidence": inv_data["final"]["confidence"],
        "aiAvailable": inv_data["aiAvailable"]
    })
    
    # 4. Investigate empty claim
    res_empty = client.post("/api/investigate", json={"claim": ""})
    assert res_empty.status_code == 400, f"Expected 400 for empty claim, got {res_empty.status_code}"
    print("[PASS] POST /api/investigate (empty claim) -> 400 error handled correctly")
    
    # 5. Investigate oversized claim
    long_claim = "A" * 1005
    res_long = client.post("/api/investigate", json={"claim": long_claim})
    assert res_long.status_code == 400, f"Expected 400 for long claim, got {res_long.status_code}"
    print("[PASS] POST /api/investigate (oversized claim) -> 400 error handled correctly")
    
    print("\nALL PHASE 1 BACKEND CONTRACT TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_phase1()
