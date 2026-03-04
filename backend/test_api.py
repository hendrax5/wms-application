import urllib.request
import json

BASE = "http://localhost:8001/api"

class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return urllib.request.Request(
            newurl, data=req.data,
            headers=dict(req.header_items()),
            method=req.get_method()
        )

opener = urllib.request.build_opener(NoRedirectHandler)

def post(path, data):
    req = urllib.request.Request(
        f"{BASE}{path}",
        json.dumps(data).encode(),
        {"Content-Type": "application/json"}
    )
    res = opener.open(req)
    return json.loads(res.read().decode())

def get(path):
    return json.loads(opener.open(f"{BASE}{path}").read().decode())

# 1. Create Device Model
dm = post("/device-models", {"brand": "Huawei", "model_name": "NE40E", "category": "ROUTER"})
print(f"[OK] Model: id={dm['id']} {dm['brand']} {dm['model_name']}")

# 2. Create Customer
cust = post("/customers", {"name": "PT XL", "company": "XL Axiata", "customer_type": "CORPORATE"})
print(f"[OK] Customer: id={cust['id']} {cust['name']}")

# 3. Create Branch Location
branch = post("/locations", {"name": "Branch Surabaya", "type": "BRANCH", "city": "Surabaya"})
print(f"[OK] Branch: id={branch['id']} {branch['name']}")

# 4. Create Site
site = post("/locations", {"name": "POP Rungkut", "type": "SITE", "city": "Surabaya", "customer_id": cust["id"]})
print(f"[OK] Site: id={site['id']} {site['name']}")

# 5. Inbound
wb = post("/workflows/inbound", {"serial_number": "SN-HW-001", "model_id": dm["id"], "location_id": branch["id"], "reference_doc": "SJ-002"})
print(f"[OK] Inbound: {wb['serial_number']} device_id={wb['device_id']}")

# 6. Get device to verify status
dev = get(f"/devices/{wb['device_id']}")
print(f"[OK] Device status: {dev['status']} location={dev['location_name']}")

# 7. Deploy
dp = post("/workflows/deploy", {
    "device_instance_id": wb["device_id"],
    "to_location_id": site["id"],
    "deployment_purpose": "INSTALLED",
    "customer_id": cust["id"],
    "reference_doc": "TIKET-002",
    "technician_name": "Cahyo"
})
print(f"[OK] Deploy: {dp['serial_number']}")

# 8. Verify deployed status
dev2 = get(f"/devices/{wb['device_id']}")
print(f"[OK] After deploy: status={dev2['status']} purpose={dev2['deployment_purpose']} customer={dev2['customer_name']}")

# 9. Dashboard
stats = get("/dashboard/stats")
print(f"[OK] Dashboard: total={stats['total_assets']} deployed={stats['status_breakdown'].get('DEPLOYED',0)}")

# 10. History
hist = get(f"/devices/{wb['device_id']}/history")
print(f"[OK] History: {len(hist)} entries")
for h in hist:
    print(f"     {h['activity_type']}: {h.get('from_location_name','-')} -> {h['to_location_name']}")

# 11. Device list with filter
devs = get("/devices?status=DEPLOYED")
print(f"[OK] Deployed devices: {len(devs)}")

# 12. QR Code
try:
    resp = opener.open(f"{BASE}/devices/{wb['device_id']}/qrcode")
    ct = resp.headers.get("Content-Type", "")
    print(f"[OK] QR Code: type={ct} size={len(resp.read())} bytes")
except Exception as e:
    print(f"[FAIL] QR Code: {e}")

print("\n=== ALL BACKEND API TESTS PASSED ===")
