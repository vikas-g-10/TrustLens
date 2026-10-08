import urllib.request
import json
import io
from PIL import Image

# 1. FastAPI direct health
r1 = urllib.request.urlopen("http://127.0.0.1:8000/api/health")
d1 = json.loads(r1.read())
print("FastAPI /api/health ->", r1.status, d1.get("version"))

# 2. Vite proxy health
r2 = urllib.request.urlopen("http://localhost:3000/api/health")
d2 = json.loads(r2.read())
print("Vite Proxy /api/health ->", r2.status, d2.get("version"))

# 3. Direct FastAPI analyze-image
img = Image.new("RGB", (120, 120), (10, 50, 90))
buf = io.BytesIO()
img.save(buf, "JPEG")
img_bytes = buf.getvalue()

boundary = "----WebKitFormBoundaryXYZ123"
body = (
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; name="file"; filename="sample.jpg"\r\n'
    f"Content-Type: image/jpeg\r\n\r\n"
).encode("utf-8") + img_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")

headers = {"Content-Type": f"multipart/form-data; boundary={boundary}"}

req3 = urllib.request.Request("http://127.0.0.1:8000/api/analyze-image", data=body, headers=headers)
with urllib.request.urlopen(req3) as r3:
    d3 = json.loads(r3.read())
    print("FastAPI /api/analyze-image ->", r3.status, "Score:", d3["evidenceHealth"]["score"], "Format:", d3["file"]["format"])

# 4. Vite proxy analyze-image
req4 = urllib.request.Request("http://localhost:3000/api/analyze-image", data=body, headers=headers)
with urllib.request.urlopen(req4) as r4:
    d4 = json.loads(r4.read())
    print("Vite Proxy /api/analyze-image ->", r4.status, "Score:", d4["evidenceHealth"]["score"])

# 5. Direct FastAPI investigate
inv_payload = json.dumps({"claim": "Live prototype verification"}).encode("utf-8")
req5 = urllib.request.Request("http://127.0.0.1:8000/api/investigate", data=inv_payload, headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req5) as r5:
    d5 = json.loads(r5.read())
    print("FastAPI /api/investigate ->", r5.status, "Verdict:", d5["final"]["verdict"])

# 6. Vite HTML Root
with urllib.request.urlopen("http://localhost:3000/") as r6:
    html = r6.read().decode()
    print("Vite Frontend HTML ->", r6.status, "Contains TrustLens:", "TrustLens" in html)

print("\nALL LIVE SERVICES AND VITE PROXY TESTS VERIFIED SUCCESSFULLY!")
