# A Hindi and a Tamil bill through Muse Glimmer

Run 2026-11-04 15:30 +0530 on this laptop's CPU, Muse Glimmer 30B Q4_K_M, the same reader and schema as English bills. The bills are test fixtures written for this check, with Latin digits and printed supplier, item and order codes. Private numbers were masked first.

| Language | Seconds | Fields correct | Wrong or missing |
| --- | --- | --- | --- |
| Hindi | 356.4 | 11 of 11 | none |
| Tamil | 456.3 | 11 of 11 | none |

```json
{
 "Hindi": {
  "supplier_id": "SUP-CALDER",
  "bill_no": "CAL-0991",
  "bill_date": "2026-11-03",
  "po_number": "PO-2003",
  "lines": [
   {
    "item_code": "CARTON-HD",
    "description": "भारी पैकिंग गत्ते का डिब्बा",
    "qty": 50.0,
    "rate_inr": 118.0,
    "amount_inr": 5900.0
   }
  ],
  "tax_inr": 1062.0,
  "total_inr": 6962.0
 },
 "Tamil": {
  "supplier_id": "SUP-CALDER",
  "bill_no": "CAL-0992",
  "bill_date": "2026-11-03",
  "po_number": "PO-2003",
  "lines": [
   {
    "item_code": "CARTON-HD",
    "description": "கனரக பேக்கிங் அட்டைப்பெட்டி",
    "qty": 50.0,
    "rate_inr": 118.0,
    "amount_inr": 5900.0
   }
  ],
  "tax_inr": 1062.0,
  "total_inr": 6962.0
 }
}
```
