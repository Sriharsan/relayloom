# Security controls: what each one costs

Every control below was run in a demo run by `python scripts/security_report.py`. A control passes only if it
blocks what it must block and lets the good input through. Times are medians on this laptop. Each control runs locally, so
none costs any money, and none needs the network.

| Level | Control | What it prevents | Passed | Median ms | Test |
| --- | --- | --- | --- | --- | --- |
| Input | Mask private numbers | A model never sees a tax id, bank account, bank code, phone or email | yes | 0.405 | `test_masking_removes_gstin_bank_ifsc_phone_and_email` |
| Input | Find hidden text in the PDF | White text that tries to give the model orders never reaches it | yes | 12.742 | `test_injection_is_recorded_and_payment_uses_master_data` |
| Input | Strict bill schema | Extra fields such as bank details, and bad values, are refused | yes | 0.058 | `test_schema_refuses_extra_keys_bank_fields_and_bad_values` |
| Decision | Policy levels | Actions that need the owner are refused without approval; changing bank details from a bill is never allowed | yes | 0.005 | `test_policy_levels_and_refusals` |
| Decision | Three way match | A bill for more than arrived is held, however it is worded | yes | 0.016 | `test_matcher_running_total_and_tolerances` |
| Decision | Repeated photo detection | The same goods photographed twice are counted once | yes | 43.65 | `test_duplicate_photo_is_found_and_different_photos_are_not` |
| Decision | Citation check | A finding that cites a record that does not exist, or a number its sources lack, is never shown | yes | 0.011 | `test_citation_of_a_missing_record_is_rejected` |
| Action | Ledger readback | A bill whose stored copy differs in any field is not treated as entered | yes | 0.004 | `test_readback_mismatch_refuses_entered_status` |
| Evidence | Signed receipts | Changing any recorded decision breaks the chain | yes | 1.979 | `test_receipts_verify_offline_and_detect_tampering` |
| Boundary | Egress gateway | Only listed hosts over HTTPS, every refusal logged | yes | 5.287 | `tests/test_gateway.py` |
| Boundary | Phone alert token | No token, no alerts, and the page can change nothing | yes | 5.031 | `tests/test_alerts.py` |
| Boundary | Phone photo intake | A photo needs the token, a size under the limit and real image bytes; nothing else is saved | yes | 5.796 | `PhotoUploadTests` |
| Decision | Agent word filter and agreement | The model's words are checked by code, and a count is accepted only when two different words agree | yes | 0.008 | `tests/test_lookagent.py` |

Together the controls add about 124.3 ms to a case. For comparison, a Muse Glimmer bill reading took a median of 326.3 s and a SAM 3.1 count 40.6 s on this CPU. The controls are about 1 part in 2624 of one bill reading, so they do not slow the work.

The latency that matters is the models', and it is shown on the Proof page with its limits.
