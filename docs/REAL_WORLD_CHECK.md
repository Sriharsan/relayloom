# Real world check

Run 2026-11-04 12:15 +0530 by `python scripts/real_world_check.py`. 85 real purchase orders from the State of California
open data (items, quantities, prices, suppliers and order numbers are rows of the public dataset), each run through `relayloom check` and `relayloom verify`
with the exception types published accounts payable sources describe.

Dataset: [State of California, Purchase Order Data 2012-2015](https://data.ca.gov/dataset/purchase-order-data). The catalog lists no licence, so only a small cited sample is kept in the repository.

| Exception type | Cases | Passed | Where the type comes from |
| --- | --- | --- | --- |
| billed above received | 80 | 80 | Sage describes an invoice for 101 laptops where the receiving report confirmed 100 |
| exact delivery | 79 | 79 | real rows with data the order system left empty |
| exact delivery, above the approval limit | 1 | 1 | real rows with data the order system left empty |
| partial shipment | 39 | 39 | Paystream and Corpay describe a purchase order for 100 units at $10 where the dock logs 90 and the vendor still bills 100 |
| price above the order | 75 | 75 | Ardent Partners: price and quantity tolerances are the main lever for match exceptions |
| row with a missing quantity or price | 5 | 5 | real rows with data the order system left empty |
| unit of measure | 10 | 10 | Peakflo and Centime describe a purchase order for 96 bottles at $7.50 invoiced as 4 cartons; both totals agree, the lines do not |
| wrong order number | 80 | 80 | Tradogram lists a PO mismatch as a standard header check |

369 of 369 cases passed.

What the real data taught the command: fractional quantities (hours and weights) need decimal counts, purchase orders go up to 12 lines so counts come from a file, some rows have no quantity or price, some names carry broken characters, and unit of measure differences need their own hint because both totals agree.

