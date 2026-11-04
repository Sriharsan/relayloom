# Command line scenarios

Run 2026-11-04 12:18 +0530 by `python scripts/package_scenarios.py`. 44 scenarios in five groups: typical deliveries, varied inputs, extreme inputs, repeated and shared use, and damaged receipts. Each runs the real command in a fresh folder.

| Group | Scenario | Expected | Result | Time |
| --- | --- | --- | --- | --- |
| typical | exact delivery | clear to enter | PASS | 95 ms |
| typical | short by one | held | PASS | 21 ms |
| typical | short by four | held | PASS | 19 ms |
| typical | short by ten percent | held | PASS | 23 ms |
| typical | delivered more than billed | clear to enter | PASS | 21 ms |
| typical | price above the order | held | PASS | 26 ms |
| typical | tax is wrong | held | PASS | 19 ms |
| typical | total is not lines plus tax | held | PASS | 41 ms |
| typical | bill cites another order | held | PASS | 23 ms |
| typical | bill from the wrong supplier | held | PASS | 21 ms |
| varied | two lines, both delivered | clear to enter | PASS | 38 ms |
| varied | two lines, the second is short | held | PASS | 31 ms |
| varied | two lines, one count missing | could not run, clear message | PASS | 29 ms |
| varied | bill lines in a different order | clear to enter | PASS | 33 ms |
| varied | a line billed that is not on the order | held | PASS | 20 ms |
| varied | photos count the second line, the first is given | clear to enter | PASS | 21 ms |
| varied | a count for a line that is not on the order | could not run, clear message | PASS | 19 ms |
| varied | kilograms with a fraction, counted short | held | PASS | 35 ms |
| varied | a folder path with spaces and accents | clear to enter | PASS | 21 ms |
| varied | a bill number with slashes and spaces | clear to enter | PASS | 31 ms |
| varied | json output for a script | held | PASS | 21 ms |
| extreme | nothing arrived | held | PASS | 20 ms |
| extreme | a million items counted | clear to enter | PASS | 22 ms |
| extreme | a negative count | could not run, clear message | PASS | 22 ms |
| extreme | a count that is not a number | could not run, clear message | PASS | 18 ms |
| extreme | a count with decimals is valid (weights, hours) | held | PASS | 21 ms |
| extreme | a bill over the owner approval limit | held | PASS | 35 ms |
| extreme | a bill number of 500 characters | could not run, clear message | PASS | 16 ms |
| extreme | a bill number that carries symbols for an instruction | could not run, clear message | PASS | 30 ms |
| extreme | bank details smuggled into the bill | could not run, clear message | PASS | 29 ms |
| extreme | an empty bill file | could not run, clear message | PASS | 15 ms |
| extreme | a purchase order that is a list | could not run, clear message | PASS | 17 ms |
| extreme | a purchase order with no lines | could not run, clear message | PASS | 14 ms |
| extreme | a bill with a quantity of zero | no crash | PASS | 35 ms |
| extreme | no count and no photos | could not run, clear message | PASS | 18 ms |
| repeated | the same check five times in one folder | held | PASS | 197 ms |
| repeated | two different bills in one folder | held | PASS | 107 ms |
| repeated | four processes writing the same folder at once | held | PASS | 710 ms |
| receipts | a receipt file with a line cut off | could not run, clear message | PASS | 79 ms |
| receipts | an empty receipt file | chain broken, caught | PASS | 75 ms |
| receipts | a middle receipt deleted | chain broken, caught | PASS | 110 ms |
| receipts | a receipt copied twice | chain broken, caught | PASS | 103 ms |
| receipts | receipts in a different order | chain broken, caught | PASS | 118 ms |
| receipts | someone else's public key | chain broken, caught | PASS | 107 ms |

44 of 44 passed in 2.5 s.
