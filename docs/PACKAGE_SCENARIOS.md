# Command line scenarios

Run 2026-11-04 15:45 +0530 by `python scripts/package_scenarios.py`. 44 scenarios in five groups: typical deliveries, varied inputs, extreme inputs, repeated and shared use, and damaged receipts. Each runs the real command in a fresh folder.

| Group | Scenario | Expected | Result | Time |
| --- | --- | --- | --- | --- |
| typical | exact delivery | clear to enter | PASS | 149 ms |
| typical | short by one | held | PASS | 14 ms |
| typical | short by four | held | PASS | 15 ms |
| typical | short by ten percent | held | PASS | 13 ms |
| typical | delivered more than billed | clear to enter | PASS | 12 ms |
| typical | price above the order | held | PASS | 12 ms |
| typical | tax is wrong | held | PASS | 14 ms |
| typical | total is not lines plus tax | held | PASS | 29 ms |
| typical | bill cites another order | held | PASS | 13 ms |
| typical | bill from the wrong supplier | held | PASS | 14 ms |
| varied | two lines, both delivered | clear to enter | PASS | 28 ms |
| varied | two lines, the second is short | held | PASS | 14 ms |
| varied | two lines, one count missing | could not run, clear message | PASS | 13 ms |
| varied | bill lines in a different order | clear to enter | PASS | 13 ms |
| varied | a line billed that is not on the order | held | PASS | 13 ms |
| varied | photos count the second line, the first is given | clear to enter | PASS | 13 ms |
| varied | a count for a line that is not on the order | could not run, clear message | PASS | 11 ms |
| varied | kilograms with a fraction, counted short | held | PASS | 26 ms |
| varied | a folder path with spaces and accents | clear to enter | PASS | 15 ms |
| varied | a bill number with slashes and spaces | clear to enter | PASS | 18 ms |
| varied | json output for a script | held | PASS | 14 ms |
| extreme | nothing arrived | held | PASS | 19 ms |
| extreme | a million items counted | clear to enter | PASS | 21 ms |
| extreme | a negative count | could not run, clear message | PASS | 11 ms |
| extreme | a count that is not a number | could not run, clear message | PASS | 11 ms |
| extreme | a count with decimals is valid (weights, hours) | held | PASS | 14 ms |
| extreme | a bill over the owner approval limit | held | PASS | 28 ms |
| extreme | a bill number of 500 characters | could not run, clear message | PASS | 12 ms |
| extreme | a bill number that carries symbols for an instruction | could not run, clear message | PASS | 11 ms |
| extreme | bank details smuggled into the bill | could not run, clear message | PASS | 9 ms |
| extreme | an empty bill file | could not run, clear message | PASS | 7 ms |
| extreme | a purchase order that is a list | could not run, clear message | PASS | 5 ms |
| extreme | a purchase order with no lines | could not run, clear message | PASS | 6 ms |
| extreme | a bill with a quantity of zero | no crash | PASS | 11 ms |
| extreme | no count and no photos | could not run, clear message | PASS | 10 ms |
| repeated | the same check five times in one folder | held | PASS | 160 ms |
| repeated | two different bills in one folder | held | PASS | 79 ms |
| repeated | four processes writing the same folder at once | held | PASS | 650 ms |
| receipts | a receipt file with a line cut off | could not run, clear message | PASS | 65 ms |
| receipts | an empty receipt file | chain broken, caught | PASS | 34 ms |
| receipts | a middle receipt deleted | chain broken, caught | PASS | 65 ms |
| receipts | a receipt copied twice | chain broken, caught | PASS | 59 ms |
| receipts | receipts in a different order | chain broken, caught | PASS | 53 ms |
| receipts | someone else's public key | chain broken, caught | PASS | 43 ms |

44 of 44 passed in 1.8 s.
