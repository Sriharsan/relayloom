"""English, Tamil and Hindi: every string exists in all three, placeholders match, scripts are the right ones, and alerts carry keys."""
import json
from pathlib import Path
import re
import unittest

from relayloom.ap import i18n
from relayloom.ap.alerts import AlertHub, PhoneInbox
from relayloom.ap.phone_page import page

TAMIL = re.compile(r"[஀-௿]")
DEVANAGARI = re.compile(r"[ऀ-ॿ]")
ROOT = Path(__file__).resolve().parents[1]


class CatalogTests(unittest.TestCase):
    def test_every_string_exists_in_all_three_languages_and_starts_unchecked(self):
        self.assertEqual(set(i18n.LANGUAGES), {"en", "ta", "hi"})
        for key, entry in i18n.STRINGS.items():
            for lang in ("en", "ta", "hi"):
                self.assertTrue(entry.get(lang, "").strip(), f"{key} has no {lang}")
            self.assertFalse(entry["checked"], f"{key} is marked checked before Sri has read it")

    def test_placeholders_are_the_same_in_every_language(self):
        for key, entry in i18n.STRINGS.items():
            wanted = i18n.placeholders(entry["en"])
            for lang in ("ta", "hi"):
                self.assertEqual(i18n.placeholders(entry[lang]), wanted, f"{key} ({lang}) changes a placeholder")

    def test_tamil_is_in_tamil_script_and_hindi_in_devanagari(self):
        for key, entry in i18n.STRINGS.items():
            words = re.sub(r"\{\w+\}|\([a-z]\)|[A-Za-z0-9_.\-]+", "", entry["ta"])
            if re.search(r"[^\W\d_]", words):  # anything left that is a letter must be Tamil
                self.assertTrue(TAMIL.search(entry["ta"]), f"{key} has no Tamil script")
            words = re.sub(r"\{\w+\}|\([a-z]\)|[A-Za-z0-9_.\-]+", "", entry["hi"])
            if re.search(r"[^\W\d_]", words):
                self.assertTrue(DEVANAGARI.search(entry["hi"]), f"{key} has no Devanagari")
            self.assertFalse(DEVANAGARI.search(entry["ta"]) or TAMIL.search(entry["hi"]), f"{key} mixes the two scripts")

    def test_translating_fills_parameters_and_translates_a_cause(self):
        self.assertEqual(i18n.t("a.needs_owner.title", "en", bill="CAL-0990"), "CAL-0990 needs you")
        self.assertIn("CAL-0990", i18n.t("a.needs_owner.title", "ta", bill="CAL-0990"))
        body = i18n.t("a.needs_owner.body", "hi", cause="Short delivery", cause_key="d.short_delivery", reason="4 billed but not received")
        self.assertIn("कम माल आया", body)
        self.assertIn("4 billed but not received", body)  # the matcher's reason stays as it is
        self.assertEqual(i18n.t("no.such.key", "ta"), "no.such.key")

    def test_the_alert_carries_english_text_the_key_and_the_parameters(self):
        made = i18n.alert("needs_owner", "a.needs_owner", bill="CAL-0990", cause="Short delivery", cause_key="d.short_delivery", reason="r")
        self.assertEqual(made["title"], "CAL-0990 needs you")
        self.assertEqual(made["key"], "a.needs_owner")
        self.assertEqual(made["params"]["cause_key"], "d.short_delivery")
        json.dumps(made)  # it must travel as JSON


class PhonePageTests(unittest.TestCase):
    def test_the_page_has_all_three_languages_a_picker_and_nothing_from_outside(self):
        html = page()
        for text in ("தமிழ்", "हिन्दी", "English", 'id="lang"', "data-i=", "relayloom-lang"):
            self.assertIn(text, html)
        self.assertNotRegex(html, r"https?://(?!127\.)")
        self.assertNotIn("</script><script", html)

    def test_every_string_the_page_uses_exists(self):
        html = page()
        used = set(re.findall(r'data-i="([\w.]+)"', html)) | set(re.findall(r'data-aria="([\w.]+)"', html)) | set(re.findall(r'"(p\.\w+)"', html))
        for key in used:
            self.assertIn(key, i18n.STRINGS, f"the phone page uses {key} but the catalog does not have it")

    def test_the_inbox_raises_keyed_alerts(self):
        import tempfile
        hub = AlertHub()
        inbox = PhoneInbox(tempfile.mkdtemp(), hub, None)
        inbox(bytes([0xFF, 0xD8, 0xFF]) + bytes(20), "image/jpeg", "box")
        self.assertEqual([a["key"] for a in hub.items], ["a.photo_received", "a.photo_saved"])


class ApprovalScreenTests(unittest.TestCase):
    def test_every_key_the_screen_uses_exists(self):
        source = (ROOT / "web" / "ap" / "app.js").read_text(encoding="utf-8") + (ROOT / "web" / "ap" / "index.html").read_text(encoding="utf-8")
        used = set(re.findall(r'\bt\("([\w.]+)"', source)) | set(re.findall(r'data-i="([\w.]+)"', source))
        for key in used:
            self.assertIn(key, i18n.STRINGS, f"the approval screen uses {key} but the catalog does not have it")
        for prefix in ("u.step.", "u.state.", "u.action.", "u.level."):  # keys built at run time
            self.assertTrue([k for k in i18n.STRINGS if k.startswith(prefix)])
        for state in ("queued", "matched", "entered_checked", "held_for_owner", "held_offline", "approved", "dispute_sent", "closed_by_owner", "readback_failed", "failed"):
            self.assertIn("u.state." + state, i18n.STRINGS)
        for action in ("send_dispute", "enter_bill", "reject_duplicate", "hold_for_recount", "enter_bill_for_received_quantity"):
            self.assertIn("u.action." + action, i18n.STRINGS)

    def test_every_status_the_server_sets_has_a_translation(self):
        source = (ROOT / "relayloom" / "ap" / "pipeline.py").read_text(encoding="utf-8")
        statuses = set(re.findall(r'(?:status = |status = \(|, )"([A-Z][A-Za-z ,;:\-]+)"', source))
        fixed = {s for s in statuses if s in ("Queued", "Reading the bill", "Counting the delivery", "Matching", "Waiting for the owner", "Investigating", "Entering the bill",
                                              "Checking the ledger", "Entered and checked", "Held, offline", "Sending the dispute")}
        for status in fixed:
            self.assertIn("s." + re.sub(r"[^a-z0-9]+", "_", status.lower()).strip("_"), i18n.STRINGS, status)


if __name__ == "__main__":
    unittest.main()
