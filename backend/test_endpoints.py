"""Quick endpoint test for ISP ERP backend."""
import urllib.request
import json

BASE = "http://localhost:8002"

endpoints = [
    ("Root", "/"),
    ("Dashboard", "/api/dashboard/stats"),
    ("Service Plans", "/api/service-plans"),
    ("Subscriptions", "/api/subscriptions"),
    ("Work Orders", "/api/work-orders"),
    ("Invoices", "/api/invoices"),
    ("Audit Logs", "/api/audit-logs"),
    ("Customers", "/api/customers"),
    ("Devices", "/api/devices"),
    ("Locations", "/api/locations"),
]

for name, path in endpoints:
    try:
        r = urllib.request.urlopen(f"{BASE}{path}")
        data = json.loads(r.read().decode())
        if isinstance(data, dict):
            print(f"  OK  {name}: keys={list(data.keys())[:6]}")
        else:
            print(f"  OK  {name}: {len(data)} items")
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        print(f"  ERR {name}: {e.code} - {body[:200]}")
    except Exception as e:
        print(f"  ERR {name}: {e}")

# Show ISP KPIs if dashboard worked
try:
    r = urllib.request.urlopen(f"{BASE}/api/dashboard/stats")
    d = json.loads(r.read().decode())
    print("\nISP KPIs:")
    for k in ["active_subscribers", "pending_activations", "monthly_recurring_revenue",
              "open_work_orders", "overdue_invoices", "total_assets"]:
        print(f"  {k}: {d.get(k, 'N/A')}")
except Exception:
    pass
