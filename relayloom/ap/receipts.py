"""Signed, chained receipts per case. Ed25519 over canonical JSON; verifiable offline."""
from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
import threading
import time

GENESIS = "0" * 64
FIELDS = ("case", "seq", "prev", "time", "agent", "step", "policy_hash", "input_hash",
          "model", "route", "response_id", "decision", "approver", "ledger_readback", "detail")


def _plain(value):
    """Whole floats become ints so Python and a browser's JSON.stringify produce the same bytes."""
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, dict):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    return value


def canonical(value) -> bytes:
    return json.dumps(_plain(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256(value) -> str:
    data = value if isinstance(value, bytes) else canonical(value)
    return hashlib.sha256(data).hexdigest()


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


class Signer:
    """Holds a local Ed25519 key. The private key never leaves its ignored file."""

    def __init__(self, key_path: Path):
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        from cryptography.hazmat.primitives import serialization
        key_path = Path(key_path)
        if key_path.exists():
            self._key = Ed25519PrivateKey.from_private_bytes(key_path.read_bytes())
        else:
            key_path.parent.mkdir(parents=True, exist_ok=True)
            self._key = Ed25519PrivateKey.generate()
            raw = self._key.private_bytes(serialization.Encoding.Raw, serialization.PrivateFormat.Raw,
                                          serialization.NoEncryption())
            key_path.write_bytes(raw)
        self.public_key = _b64(self._key.public_key().public_bytes(serialization.Encoding.Raw,
                                                                    serialization.PublicFormat.Raw))

    def sign(self, data: bytes) -> str:
        return _b64(self._key.sign(data))


class ReceiptChain:
    """Append-only receipts, one hash chain per case, written as JSON lines."""

    def __init__(self, path: Path, signer: Signer, policy_hash: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.signer = signer
        self.policy_hash = policy_hash
        self.lock = threading.Lock()
        self.heads: dict[str, tuple[int, str]] = {}
        if self.path.exists():
            for receipt in self.read():
                self.heads[receipt["body"]["case"]] = (receipt["body"]["seq"], receipt["hash"])

    def append(self, case: str, agent: str, step: str, decision: str, *, input_hash: str = "",
               model: str = "", route: str = "", response_id: str = "", approver: str = "",
               ledger_readback: str = "", detail: dict | None = None) -> dict:
        with self.lock:
            seq, prev = self.heads.get(case, (0, GENESIS))
            body = {"case": case, "seq": seq + 1, "prev": prev, "time": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    "agent": agent, "step": step, "policy_hash": self.policy_hash, "input_hash": input_hash,
                    "model": model, "route": route, "response_id": response_id, "decision": decision,
                    "approver": approver, "ledger_readback": ledger_readback, "detail": detail or {}}
            data = canonical(body)
            receipt = {"body": body, "hash": hashlib.sha256(data).hexdigest(), "sig": self.signer.sign(data)}
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(receipt, ensure_ascii=False) + "\n")
            self.heads[case] = (body["seq"], receipt["hash"])
            return receipt

    def read(self, case: str | None = None) -> list[dict]:
        if not self.path.exists():
            return []
        rows = [json.loads(line) for line in self.path.read_text(encoding="utf-8").splitlines() if line.strip()]
        return [row for row in rows if case is None or row["body"]["case"] == case]


def verify(receipts: list[dict], public_key_b64: str) -> tuple[bool, list[str]]:
    """Check signature, hash and chain order for every case. Needs no network."""
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    from cryptography.exceptions import InvalidSignature
    key = Ed25519PublicKey.from_public_bytes(base64.b64decode(public_key_b64))
    problems, heads = [], {}
    for index, receipt in enumerate(receipts):
        body = receipt.get("body", {})
        if set(body) != set(FIELDS):
            problems.append(f"receipt {index}: unexpected fields")
            continue
        data = canonical(body)
        if hashlib.sha256(data).hexdigest() != receipt.get("hash"):
            problems.append(f"receipt {index}: hash does not match body")
        try:
            key.verify(base64.b64decode(receipt.get("sig", "")), data)
        except (InvalidSignature, ValueError):
            problems.append(f"receipt {index}: bad signature")
        seq, prev = heads.get(body["case"], (0, GENESIS))
        if body["seq"] != seq + 1 or body["prev"] != prev:
            problems.append(f"receipt {index}: chain broken for case {body['case']}")
        heads[body["case"]] = (body["seq"], receipt.get("hash"))
    return not problems, problems
