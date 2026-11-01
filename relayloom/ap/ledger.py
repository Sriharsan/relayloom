"""One ledger interface: ERPNext over its REST API, or a small built in ledger with the same calls."""
from __future__ import annotations

import json
from pathlib import Path
import sqlite3
import threading
import urllib.error
import urllib.parse
import urllib.request


class LedgerOffline(Exception):
    """The ledger could not be reached. Nothing is assumed about what happened there."""


class LocalLedger:
    """SQLite ledger for judges without Docker. Same calls and readback shape as ERPNextLedger."""

    name = "LocalLedger"

    def __init__(self, path: Path | str = ":memory:"):
        self.db = sqlite3.connect(str(path), check_same_thread=False)
        self.lock = threading.Lock()
        self.online = True
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS supplier (id TEXT PRIMARY KEY, body TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS po (po_number TEXT PRIMARY KEY, body TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS invoice (id TEXT PRIMARY KEY, supplier_id TEXT NOT NULL, bill_no TEXT NOT NULL,
                body TEXT NOT NULL, UNIQUE (supplier_id, bill_no));
        """)

    def _check(self):
        if not self.online:
            raise LedgerOffline("local ledger link is cut")

    def seed(self, suppliers: list[dict], pos: list[dict], history: list[dict] = ()):
        with self.lock, self.db:
            for supplier in suppliers:
                self.db.execute("INSERT OR REPLACE INTO supplier VALUES (?, ?)", (supplier["id"], json.dumps(supplier)))
            for po in pos:
                self.db.execute("INSERT OR REPLACE INTO po VALUES (?, ?)", (po["po_number"], json.dumps(po)))
            for old in history:
                entry = {"supplier_id": old["supplier_id"], "bill_no": old["bill_no"], "bill_date": old["bill_date"],
                         "po_number": old["po_number"], "tax_inr": old["tax_inr"], "total_inr": old["total_inr"],
                         "lines": [{"item_code": old["item_code"], "qty": old["qty"], "rate_inr": old["rate_inr"],
                                    "amount_inr": round(old["qty"] * old["rate_inr"], 2)}]}
                self.db.execute("INSERT OR REPLACE INTO invoice VALUES (?, ?, ?, ?)",
                                (old["id"], old["supplier_id"], old["bill_no"], json.dumps(entry)))

    def invoices(self, supplier_id: str | None = None, po_number: str | None = None) -> list[dict]:
        """Invoices already in the books, newest first, in one shape for both ledgers."""
        self._check()
        with self.lock:
            rows = self.db.execute("SELECT id, body FROM invoice").fetchall()
        found = []
        for invoice_id, body in rows:
            entry = json.loads(body)
            if (supplier_id and entry["supplier_id"] != supplier_id) or (po_number and entry["po_number"] != po_number):
                continue
            found.append({"id": invoice_id, **entry})
        return sorted(found, key=lambda e: e["bill_date"], reverse=True)

    def get_supplier(self, supplier_id: str) -> dict | None:
        self._check()
        with self.lock:
            row = self.db.execute("SELECT body FROM supplier WHERE id = ?", (supplier_id,)).fetchone()
        return json.loads(row[0]) if row else None

    def get_po(self, po_number: str) -> dict | None:
        self._check()
        with self.lock:
            row = self.db.execute("SELECT body FROM po WHERE po_number = ?", (po_number,)).fetchone()
        return json.loads(row[0]) if row else None

    def find_invoice(self, supplier_id: str, bill_no: str) -> str | None:
        self._check()
        with self.lock:
            row = self.db.execute("SELECT id FROM invoice WHERE supplier_id = ? AND bill_no = ?",
                                  (supplier_id, bill_no)).fetchone()
        return row[0] if row else None

    def create_invoice(self, entry: dict) -> str:
        self._check()
        with self.lock, self.db:
            count = self.db.execute("SELECT COUNT(*) FROM invoice").fetchone()[0]
            invoice_id = f"LOCAL-PINV-{count + 1:04d}"
            self.db.execute("INSERT INTO invoice VALUES (?, ?, ?, ?)",
                            (invoice_id, entry["supplier_id"], entry["bill_no"], json.dumps(entry)))
        return invoice_id

    def read_invoice(self, invoice_id: str) -> dict | None:
        self._check()
        with self.lock:
            row = self.db.execute("SELECT body FROM invoice WHERE id = ?", (invoice_id,)).fetchone()
        return json.loads(row[0]) if row else None

    def count_invoices(self, supplier_id: str, bill_no: str) -> int:
        with self.lock:
            return self.db.execute("SELECT COUNT(*) FROM invoice WHERE supplier_id = ? AND bill_no = ?",
                                   (supplier_id, bill_no)).fetchone()[0]


class ERPNextLedger:
    """ERPNext through /api/resource with an API key and secret from the environment."""

    name = "ERPNext"

    def __init__(self, url: str, key: str, secret: str, company: str, timeout: float = 240):
        parts = urllib.parse.urlsplit(url)
        if parts.scheme != "http" or parts.hostname not in ("localhost", "127.0.0.1", "erpnext", "frontend"):
            raise ValueError("ERPNext must be the local instance inside the boundary")
        self.url = url.rstrip("/")
        self._auth = f"token {key}:{secret}"
        self.company = company
        self.timeout = timeout
        self.online = True
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def __repr__(self):
        return f"ERPNextLedger(url={self.url!r}, company={self.company!r}, key=<hidden>)"

    def _call(self, method: str, path: str, body: dict | None = None, query: dict | None = None):
        if not self.online:
            raise LedgerOffline("ledger link is cut")
        url = self.url + path + ("?" + urllib.parse.urlencode(query) if query else "")
        data = json.dumps(body).encode() if body is not None else None
        request = urllib.request.Request(url, data=data, method=method, headers={
            "Authorization": self._auth, "Accept": "application/json", "Content-Type": "application/json"})
        try:
            with self.opener.open(request, timeout=self.timeout) as response:
                return json.loads(response.read() or b"{}")
        except urllib.error.HTTPError as error:
            if error.code == 404:
                return None
            detail = error.read()[:400].decode("utf-8", "replace")
            raise RuntimeError(f"ERPNext {method} {path} returned {error.code}: {detail}") from None
        except (urllib.error.URLError, TimeoutError, ConnectionError) as error:
            raise LedgerOffline(f"ERPNext unreachable: {type(error).__name__}") from None

    def resource(self, doctype: str, name: str | None = None):
        path = "/api/resource/" + urllib.parse.quote(doctype)
        return path + ("/" + urllib.parse.quote(name, safe="") if name else "")

    def get(self, doctype: str, name: str):
        result = self._call("GET", self.resource(doctype, name))
        return result["data"] if result else None

    def insert(self, doctype: str, doc: dict):
        return self._call("POST", self.resource(doctype), doc)["data"]

    def list(self, doctype: str, filters: list, fields: list):
        result = self._call("GET", self.resource(doctype), query={
            "filters": json.dumps(filters), "fields": json.dumps(fields), "limit_page_length": 100})
        return result["data"]

    def get_supplier(self, supplier_id: str) -> dict | None:
        doc = self.get("Supplier", supplier_id)
        if not doc:
            return None
        banks = self.list("Bank Account", [["party_type", "=", "Supplier"], ["party", "=", supplier_id]],
                          ["bank_account_no", "branch_code", "is_default"])
        bank = next((row for row in banks if row.get("is_default")), banks[0] if banks else {})
        return {"id": doc["name"], "name": doc["supplier_name"], "gstin": doc.get("tax_id") or "",
                "bank_account": bank.get("bank_account_no", ""), "ifsc": bank.get("branch_code", "")}

    def po_name(self, po_number: str) -> str | None:
        """ERPNext names orders from its own series; the number printed on bills is the title."""
        rows = self.list("Purchase Order", [["title", "=", po_number], ["docstatus", "=", 1]], ["name"])
        return rows[0]["name"] if rows else None

    def get_po(self, po_number: str) -> dict | None:
        name = self.po_name(po_number)
        doc = self.get("Purchase Order", name) if name else None
        if not doc:
            return None
        net = sum(row["amount"] for row in doc["items"]) or 1
        return {"po_number": doc["title"], "erpnext_name": doc["name"], "supplier_id": doc["supplier"],
                "tax_rate": round(doc.get("total_taxes_and_charges", 0) / net, 4),
                "items": [{"item_code": row["item_code"], "description": row["item_name"], "qty": row["qty"],
                           "rate_inr": row["rate"]} for row in doc["items"]]}

    def invoices(self, supplier_id: str | None = None, po_number: str | None = None) -> list[dict]:
        filters = [["docstatus", "<", 2]] + ([["supplier", "=", supplier_id]] if supplier_id else [])
        rows = self.list("Purchase Invoice", filters, ["name"])
        found = []
        for row in rows:
            entry = self.read_invoice(row["name"])
            if entry and (not po_number or entry["po_number"] == po_number):
                found.append({"id": row["name"], **entry})
        return sorted(found, key=lambda e: e["bill_date"], reverse=True)

    def find_invoice(self, supplier_id: str, bill_no: str) -> str | None:
        rows = self.list("Purchase Invoice", [["supplier", "=", supplier_id], ["bill_no", "=", bill_no],
                                              ["docstatus", "<", 2]], ["name"])
        return rows[0]["name"] if rows else None

    def count_invoices(self, supplier_id: str, bill_no: str) -> int:
        return len(self.list("Purchase Invoice", [["supplier", "=", supplier_id], ["bill_no", "=", bill_no],
                                                  ["docstatus", "<", 2]], ["name"]))

    def create_invoice(self, entry: dict) -> str:
        po_name = self.po_name(entry["po_number"])
        doc = {"doctype": "Purchase Invoice", "company": self.company, "supplier": entry["supplier_id"],
               "bill_no": entry["bill_no"], "bill_date": entry["bill_date"], "posting_date": entry["bill_date"],
               "set_posting_time": 1, "due_date": entry["bill_date"],
               "remarks": f"Entered by Relayloom Clerk. Case {entry['case']}. Paid to supplier master bank only.",
               "items": [{"item_code": line["item_code"], "qty": line["qty"], "rate": line["rate_inr"],
                          "purchase_order": po_name} for line in entry["lines"]],
               "taxes": [{"charge_type": "On Net Total", "account_head": entry["tax_account"],
                          "description": "GST", "rate": round(entry["tax_rate"] * 100, 2)}] if entry.get("tax_account") else []}
        return self.insert("Purchase Invoice", doc)["name"]

    def read_invoice(self, invoice_id: str) -> dict | None:
        doc = self.get("Purchase Invoice", invoice_id)
        if not doc:
            return None
        po_name = next((row.get("purchase_order") for row in doc["items"] if row.get("purchase_order")), "")
        po = self.get("Purchase Order", po_name)["title"] if po_name else ""
        return {"supplier_id": doc["supplier"], "bill_no": doc["bill_no"], "bill_date": doc["bill_date"],
                "po_number": po, "lines": [{"item_code": row["item_code"], "qty": row["qty"], "rate_inr": row["rate"],
                                             "amount_inr": row["amount"]} for row in doc["items"]],
                "tax_inr": doc.get("total_taxes_and_charges", 0), "total_inr": doc["grand_total"],
                "docstatus": doc["docstatus"]}
