"""Every command line scenario in tests/scenarios.py must behave as listed."""
import re
import unittest

from scenarios import SCENARIOS, run_scenario


class ScenarioTests(unittest.TestCase):
    def test_every_scenario(self):
        failures = []
        for group, name, spec, expected, phrase in SCENARIOS:
            code, text = run_scenario(group, name, spec, expected, phrase)
            ok_code = expected is None or code == expected
            if not (ok_code and re.search(phrase, text) and "Traceback" not in text):
                failures.append(f"[{group}] {name}: exit {code}, wanted {expected}, phrase {phrase!r}: {text.strip()[:160]}")
        self.assertEqual(failures, [], "\n" + "\n".join(failures))

    def test_there_are_at_least_forty_scenarios_in_five_groups(self):
        self.assertGreaterEqual(len(SCENARIOS), 40)
        self.assertEqual({s[0] for s in SCENARIOS}, {"typical", "varied", "extreme", "repeated", "receipts"})


if __name__ == "__main__":
    unittest.main()
