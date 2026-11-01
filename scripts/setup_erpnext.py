"""Prepare the local ERPNext from frappe_docker pwd.yml for Relayloom. Synthetic records only.

1. Logs in as Administrator. If the default password still works, replaces it with a random one.
2. Completes the setup wizard for the synthetic company (India, INR).
3. Creates a Relayloom user with an API key and secret.
4. Seeds suppliers, bank accounts, items, a GST account and submitted purchase orders over /api/resource.
New secrets are written only to .env (git ignored). Nothing secret is printed.
"""
import http.cookiejar
import json
from pathlib import Path
import secrets
import sys
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / ".env"
DATA = json.loads((ROOT / "fixtures" / "data.json").read_text(encoding="utf-8"))
URL = "http://localhost:8080"
ABBR = "NGC"
COMPANY = DATA["company"]["name"]


def env():
    values = {}
    for line in ENV.read_text(encoding="utf-8").splitlines() if ENV.exists() else []:
        name, sep, value = line.partition("=")
        if sep and not name.startswith("#"):
            values[name.strip()] = value.strip()
    return values


def set_env(name, value):
    """Change one key's line in place, or append it. Every other line, HF_TOKEN included, is kept as is."""
    text = ENV.read_text(encoding="utf-8") if ENV.exists() else ""
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if line.startswith(name + "="):
            lines[index] = f"{name}={value}"
            break
    else:
        lines.append(f"{name}={value}")
    ENV.write_text("\n".join(lines) + "\n", encoding="utf-8")


class Client:
    def __init__(self, auth=None):
        self.jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), urllib.request.HTTPCookieProcessor(self.jar))
        self.auth = auth

    def call(self, method, path, body=None, form=False, quiet404=False):
        headers = {"Accept": "application/json"}
        if self.auth:
            headers["Authorization"] = self.auth
        if body is not None and form:
            data = urllib.parse.urlencode(body).encode()
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        elif body is not None:
            data = json.dumps(body).encode()
            headers["Content-Type"] = "application/json"
        else:
            data = None
        request = urllib.request.Request(URL + path, data=data, method=method, headers=headers)
        try:
            with self.opener.open(request, timeout=300) as response:
                return json.loads(response.read() or b"{}")
        except urllib.error.HTTPError as error:
            if quiet404 and error.code == 404:
                return None
            text = error.read().decode("utf-8", "replace")
            raise RuntimeError(f"{method} {path} -> {error.code}: {text[:600]}") from None

    def login(self, password):
        try:
            self.call("POST", "/api/method/login", {"usr": "Administrator", "pwd": password}, form=True)
            return True
        except RuntimeError:
            return False

    def exists(self, doctype, name):
        return self.call("GET", f"/api/resource/{urllib.parse.quote(doctype)}/{urllib.parse.quote(name, safe='')}", quiet404=True) is not None

    def insert(self, doc):
        return self.call("POST", f"/api/resource/{urllib.parse.quote(doc['doctype'])}", doc)["data"]


def main():
    values = env()
    admin = Client()
    password = values.get("ERPNEXT_ADMIN_PASSWORD") or "admin"
    if not admin.login(password):
        sys.exit("Administrator login failed. Set ERPNEXT_ADMIN_PASSWORD in .env to the current password.")
    if password == "admin":
        new = secrets.token_urlsafe(18)
        admin.call("POST", "/api/method/frappe.core.doctype.user.user.update_password",
                   {"new_password": new, "old_password": "admin"}, form=True)
        set_env("ERPNEXT_ADMIN_PASSWORD", new)
        print("Default Administrator password replaced; new one saved to .env")
        admin = Client()
        if not admin.login(new):
            sys.exit("Login with the new password failed")

    if not admin.exists("Company", COMPANY):
        print("Running the setup wizard (a few minutes)")
        args = {"language": "English", "country": "India", "timezone": "Asia/Kolkata", "currency": "INR",
                "full_name": "Relayloom Admin", "email": "admin@relayloom.invalid", "company_name": COMPANY,
                "company_abbr": ABBR, "chart_of_accounts": "Standard", "fy_start_date": "2026-04-01",
                "fy_end_date": "2027-03-31", "setup_demo": 0}
        admin.call("POST", "/api/method/frappe.desk.page.setup_wizard.setup_wizard.setup_complete",
                   {"args": json.dumps(args)}, form=True)

    user = "relayloom.agent@relayloom.invalid"
    if not admin.exists("User", user):
        admin.insert({"doctype": "User", "email": user, "first_name": "Relayloom", "last_name": "Agents",
                      "send_welcome_email": 0, "user_type": "System User",
                      "roles": [{"role": r} for r in ("Accounts Manager", "Accounts User", "Purchase Manager",
                                                       "Purchase User", "Stock User", "Item Manager")]})
    if not values.get("ERPNEXT_API_SECRET"):
        secret = admin.call("POST", "/api/method/frappe.core.doctype.user.user.generate_keys", {"user": user}, form=True)["message"]["api_secret"]
        key = admin.call("GET", f"/api/resource/User/{urllib.parse.quote(user)}")["data"]["api_key"]
        set_env("ERPNEXT_API_KEY", key)
        set_env("ERPNEXT_API_SECRET", secret)
        print("API key and secret for the Relayloom user saved to .env")
    set_env("ERPNEXT_COMPANY", COMPANY)
    set_env("ERPNEXT_TAX_ACCOUNT", f"Input GST - {ABBR}")

    values = env()
    api = Client(f"token {values['ERPNEXT_API_KEY']}:{values['ERPNEXT_API_SECRET']}")
    seed(admin, admin)
    print("Seeded synthetic suppliers, bank accounts, items, GST account and purchase orders")


def seed(api, admin):
    """Master data is seeded as Administrator. The agent user only creates and reads purchase invoices."""
    tax_account = f"Input GST - {ABBR}"
    if not admin.exists("Account", tax_account):
        admin.insert({"doctype": "Account", "account_name": "Input GST", "parent_account": f"Duties and Taxes - {ABBR}",
                    "company": COMPANY, "account_type": "Tax", "is_group": 0})
    if not admin.exists("Bank", "Synthetic Bank"):
        admin.insert({"doctype": "Bank", "bank_name": "Synthetic Bank"})
    for code, spec in DATA["items"].items():
        if not api.exists("Item", code):
            api.insert({"doctype": "Item", "item_code": code, "item_name": spec["name"], "item_group": "Raw Material",
                        "stock_uom": "Nos", "is_stock_item": 0, "is_purchase_item": 1})
    for supplier in DATA["suppliers"]:
        if not api.exists("Supplier", supplier["id"]):
            doc = api.insert({"doctype": "Supplier", "supplier_name": supplier["name"],
                              "supplier_group": "Raw Material", "tax_id": supplier["gstin"], "country": "India"})
            # Frappe names suppliers by supplier_name by default; rename to the id the bills print.
            if doc["name"] != supplier["id"]:
                api.call("POST", "/api/method/frappe.client.rename_doc",
                         {"doctype": "Supplier", "old_name": doc["name"], "new_name": supplier["id"]})
        rows = api.call("GET", "/api/resource/Bank%20Account?" + urllib.parse.urlencode(
            {"filters": json.dumps([["party", "=", supplier["id"]]])}))["data"]
        if not rows:
            api.insert({"doctype": "Bank Account", "account_name": supplier["name"], "bank": "Synthetic Bank",
                        "party_type": "Supplier", "party": supplier["id"], "bank_account_no": supplier["bank_account"],
                        "branch_code": supplier["ifsc"], "is_default": 1})
    for po in DATA["purchase_orders"]:
        found = api.call("GET", "/api/resource/Purchase%20Order?" + urllib.parse.urlencode(
            {"filters": json.dumps([["title", "=", po["po_number"]], ["docstatus", "=", 1]])}))["data"]
        if found:
            continue
        # ERPNext names orders from its own series; the number on our bills is kept in the title.
        api.insert({"doctype": "Purchase Order", "title": po["po_number"],
                    "supplier": po["supplier_id"], "company": COMPANY, "transaction_date": "2026-10-27",
                    "schedule_date": "2026-10-29", "docstatus": 1,
                    "items": [{"item_code": i["item_code"], "qty": i["qty"], "rate": i["rate_inr"],
                               "schedule_date": "2026-10-29"} for i in po["items"]],
                    "taxes": [{"charge_type": "On Net Total", "account_head": tax_account, "description": "GST",
                               "rate": round(po["tax_rate"] * 100, 2), "category": "Total", "add_deduct_tax": "Add"}]})
    seed_history(tax_account)


def seed_history(tax_account):
    """Earlier invoices for the Investigator to cite (last price paid, duplicates, billed so far on an order)."""
    sys.path.insert(0, str(ROOT))
    from relayloom.ap.ledger import ERPNextLedger
    values = env()
    ledger = ERPNextLedger(URL, values["ERPNEXT_API_KEY"], values["ERPNEXT_API_SECRET"], COMPANY)
    for old in DATA["history_invoices"]:
        if ledger.find_invoice(old["supplier_id"], old["bill_no"]):
            continue
        po = next(p for p in DATA["purchase_orders"] if p["po_number"] == old["po_number"])
        ledger.create_invoice({"case": "earlier invoice", "supplier_id": old["supplier_id"], "bill_no": old["bill_no"],
                               "bill_date": old["bill_date"], "po_number": old["po_number"],
                               "lines": [{"item_code": old["item_code"], "qty": old["qty"], "rate_inr": old["rate_inr"],
                                          "amount_inr": round(old["qty"] * old["rate_inr"], 2)}],
                               "tax_rate": po["tax_rate"], "tax_account": tax_account, "posting_date": "2026-10-29"})
        print("earlier invoice", old["bill_no"], flush=True)


if __name__ == "__main__":
    main()
