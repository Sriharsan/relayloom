"""Write the documented real cases to docs/real_cases.json, site-src/src/data/cases.json and the Real cases section of docs/SOURCES.md.

Every case below was read at its source on 4 November 2026 (pages in a browser, the Interior OIG summary as a PDF with a text extractor).
They are documented cases from courts, audits and news, not Relayloom users. Two cases from the list could not be read and are not used:
the Zimbabwe councils article sits behind a bot check that was not bypassed, and the ERP forum thread no longer exists.
"""
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]

CASES = [
    {"id": "nj-allied", "kind": "court", "status": "convicted", "place": "United States, New Jersey", "figure": "USD 9.5 million", "short": "ordered back to the customer",
     "title": "A supplier billed for goods it never delivered, for almost nine years",
     "text": "Between 2009 and April 2018 the owner of Allied Materials sent invoices that listed products Allied had not delivered and inflated the quantities it did deliver. He was sentenced to 50 months in prison and ordered to pay USD 9.5 million in restitution to the customer. The release also says he paid people at the customer to get the invoices accepted.",
     "source": "U.S. Attorney's Office, District of New Jersey, press release 19-209", "date": "17 July 2019",
     "url": "https://www.justice.gov/usao-nj/pr/owner-janitorial-supply-company-sentenced-50-months-prison-defrauding-customer-failing"},
    {"id": "iskcon", "kind": "news", "status": "alleged", "place": "India, Kolkata", "figure": "Rs 2 crore", "short": "alleged, found in an audit",
     "title": "A book supplier is accused of billing full orders and delivering fewer books",
     "text": "Police say a supplier billed ISKCON Kolkata for full orders and delivered fewer books. The fraud was uncovered in a later audit, and the accused was taken into custody. It is an allegation; the article reports an investigation, not a conviction. The article is dated 10 November 2025.",
     "source": "Devdiscourse", "date": "10 November 2025",
     "url": "https://www.devdiscourse.com/article/law-order/3691327-fake-invoices-scandal-book-supplier-arrested-for-defrauding-iskcon-kolkata"},
    {"id": "blm", "kind": "audit", "status": "substantiated", "place": "United States, federal government", "figure": "USD 20,720", "short": "paid for 8 units, 1 delivered",
     "title": "A federal office paid for eight units and received one",
     "text": "The Interior Department's Inspector General substantiated that the Bureau of Land Management paid a vendor USD 20,720 for eight backup power supply units and received one. BLM paid the full amount by mistake, and its later attempts to get the other seven units or a refund failed.",
     "source": "U.S. Department of the Interior, Office of Inspector General, investigative summary", "date": "6 January 2017",
     "url": "https://www.oversight.gov/sites/default/files/documents/reports/2017-11/InvestigativeSummary_BLMPaymentForProductsNotDelivered.pdf"},
    {"id": "airmatic", "kind": "court", "status": "convicted", "place": "United States, Philadelphia", "figure": "USD 556,633", "short": "restitution to the city",
     "title": "Invoices named approved items while other goods arrived at about 87 percent higher prices",
     "text": "Airmatic pleaded guilty to mail fraud. Its invoices billed items approved under the city's contract while it delivered other, off-contract goods, inflating the cost by about 87 percent on average. In one case the city was invoiced for a bearing assembly and received 12 asphalt rakes. The court ordered USD 556,633.03 in restitution.",
     "source": "U.S. Attorney's Office, Eastern District of Pennsylvania", "date": "10 December 2014",
     "url": "https://www.justice.gov/usao-edpa/pr/malvern-company-sentenced-defrauding-city-philadelphia-and-debarred-city-business"},
    {"id": "anj", "kind": "news", "status": "alleged", "place": "India, Mumbai", "figure": "Rs 3.82 crore", "short": "alleged, 17 invoices flagged",
     "title": "An interior firm alleges fake purchase orders and invoices for materials never delivered",
     "text": "A police case says three employees and three vendors of ANJ Turnkey Projects raised fake purchase orders and invoices for materials that were allegedly never delivered to its Wada factory. The firm's internal audit flagged 17 invoices. It is an allegation under investigation.",
     "source": "Free Press Journal", "date": "7 October 2026",
     "url": "https://www.freepressjournal.in/mumbai/mumbai-382-crore-fraud-alleged-at-interior-firm-3-employees-and-3-vendors-booked"},
    {"id": "nagaland-agri", "kind": "audit", "status": "audit finding", "place": "India, Nagaland", "figure": "Rs 7.20 crore", "short": "excess payment",
     "title": "A supplier did not supply the full quantity of brush cutters and was paid in full",
     "text": "The Comptroller and Auditor General's report for the year ending March 2022 found that the Agriculture Department paid a supplier in full although the full quantity of brush cutters was not supplied, an excess payment of Rs 7.20 crore. The article gives conflicting unit counts, so none are repeated here.",
     "source": "The Morung Express, reporting the CAG report", "date": "25 September 2023",
     "url": "https://morungexpress.com/nagaland-cag-flags-excess-payment-of-rs-720-cr-by-agri-dept-for-machineries"},
    {"id": "nagaland-rd", "kind": "audit", "status": "audit finding", "place": "India, Nagaland", "figure": "Rs 6.21 crore", "short": "no record of receipt",
     "title": "Diggers and tent umbrellas paid for with no record that they arrived",
     "text": "The CAG's 2017 to 18 audit of the Rural Development Department found Rs 6.21 crore paid for post hole diggers and tent umbrellas without any record of receipt, part of Rs 20.89 crore it called fraudulent payments. The diggers were paid in full with no entries in the receipt registers.",
     "source": "The Morung Express, reporting the CAG report", "date": "19 February 2020",
     "url": "https://morungexpress.com/nagaland-fraudulent-payments-rs-2089-cr-rd-department"},
    {"id": "mass-school", "kind": "audit", "status": "audit finding", "place": "United States, Massachusetts", "figure": "12 of 60", "short": "payments with no receiving report",
     "title": "A school paid vendors without proof the goods arrived",
     "text": "The State Auditor sampled 60 vendor payments at the Helen Y. Davis Leadership Academy Charter Public School. Twelve had no receiving report, the evidence that goods arrived. Fifty-six had no approved purchase order, and three had no supporting documents at all.",
     "source": "Office of the State Auditor of Massachusetts", "date": "19 November 2018",
     "url": "https://www.mass.gov/info-details/vendor-invoices-totaling-thousands-of-dollars-were-processed-without-required-supporting-documentation"},
    {"id": "fsr", "kind": "news", "status": "analysis", "place": "United States, restaurants", "figure": "35 percent", "short": "of invoices had an overcharge",
     "title": "At least one overcharge on 35 percent of restaurant invoices",
     "text": "Consolidated Concepts analysed more than 11,000 invoices from 400 restaurants in 2015 and found at least one overcharge on 35 percent of them, typically about 1 percent of the invoice total. These are overcharges, not short deliveries, and the data is from 2015.",
     "source": "FSR Magazine", "date": "2 December 2015",
     "url": "https://www.fsrmagazine.com/finance/overcharges-continue-show-restaurant-invoices"},
    {"id": "lpg", "kind": "news", "status": "enforcement", "place": "India, Andhra Pradesh", "figure": "170 g to 2.1 kg", "short": "short in 14.2 kg cylinders",
     "title": "Domestic gas cylinders delivered underweight",
     "text": "In March 2026 the Legal Metrology department booked 17 cases and fined each Rs 25,000 after finding discrepancies of 170 grams to 2.1 kilograms in 14.2 kilogram domestic cylinders. Three of the 17 cases concern weighing machines that were not certified.",
     "source": "Deccan Chronicle", "date": "1 April 2026",
     "url": "https://deccanchronicle.com/southern-states/andhra-pradesh/underweight-lpg-cylinders-a-new-offshoot-of-gas-shortage-1947695"},
    {"id": "markets", "kind": "news", "status": "enforcement", "place": "India, Andhra Pradesh", "figure": "172 cases", "short": "booked for short weight and other violations",
     "title": "Raids on vegetable markets for short weight",
     "text": "Legal Metrology teams raided Rythu Bazars, vegetable markets and other traders across the state and booked 172 cases against wholesale and retail traders for short weight and other violations of the Legal Metrology Act. The article is dated March 2024.",
     "source": "The Hindu, via inkl", "date": "21 March 2024",
     "url": "https://www.inkl.com/news/172-cases-booked-against-vendors-for-short-weight-other-violations-in-state"},
]
UNREAD = [
    ("Zimbabwe, 10 local councils, Auditor General 2024: nearly USD 1 million paid for goods never delivered", "https://www.heraldonline.co.zw/councils-pay-us1m-for-goods-never-delivered/",
     "The page sits behind a bot check that was not bypassed, so it could not be read."),
    ("An ERP forum post: 55 units received against an order for 50", "https://epiusers.help/t/a-p-and-receiving-mistakes/10850", "The thread no longer exists or is private."),
]


def main():
    (ROOT / "docs" / "real_cases.json").write_text(json.dumps({"checked": "2026-11-04", "cases": CASES, "not_used": UNREAD}, indent=1, ensure_ascii=False), encoding="utf-8")
    (ROOT / "site-src" / "src" / "data" / "cases.json").write_text(json.dumps({"cases": CASES}, indent=1, ensure_ascii=False), encoding="utf-8")
    block = ["<!-- real-cases:start -->", "## Real cases: paying for goods that did not arrive", "",
             "Documented cases from courts, audits and news, read at their sources on 4 November 2026. They are not Relayloom users. "
             "Where a source calls a case an allegation, it is shown as one.", ""]
    for c in CASES:
        block += [f"- **{c['place']}, {c['figure']} ({c['status']}).** {c['title']}. {c['text']} Source: [{c['source']}, {c['date']}]({c['url']})."]
    block += ["", "Not used, because they could not be read at the source:"]
    block += [f"- {t}: <{u}>. {why}" for t, u, why in UNREAD]
    block += ["<!-- real-cases:end -->", ""]
    sources = ROOT / "docs" / "SOURCES.md"
    text = sources.read_text(encoding="utf-8")
    text = re.sub(r"<!-- real-cases:start -->.*?<!-- real-cases:end -->\n?", "", text, flags=re.S).rstrip() + "\n\n" + "\n".join(block)
    sources.write_text(text, encoding="utf-8")
    print(len(CASES), "cases written")


if __name__ == "__main__":
    main()
