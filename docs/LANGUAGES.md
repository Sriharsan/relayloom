# Languages: English, Tamil, Hindi

Every phone alert and approval screen string, approved for release by Sri. English is the source. Edit a Tamil or Hindi word in `scripts/make_strings.py`, then regenerate: read the Tamil and the Hindi, fix any word, and tick the last column. `{like_this}` is filled in by the app; leave it as it is.

Open any screen with `?review=1` to underline any string marked unchecked.

Not translated, on purpose: text written by the model or taken from the bill (the finding, the dispute text, the bill text), the reason a bill is held (made by the matcher from the numbers), and the Boundary and Benchmark screens. The screens say so.

| Key | English | தமிழ் | हिन्दी | Checked by Sri |
| --- | --- | --- | --- | --- |
| `p.title` | Relayloom alerts | Relayloom அறிவிப்புகள் | Relayloom सूचनाएँ | ☐ |
| `p.connecting` | Connecting | இணைக்கப்படுகிறது | जुड़ रहा है | ☐ |
| `p.waiting` | Connected, waiting for deliveries | இணைக்கப்பட்டது, சரக்கு வருகைக்காகக் காத்திருக்கிறது | जुड़ गया, माल आने की प्रतीक्षा है | ☐ |
| `p.reconnecting` | Reconnecting | மீண்டும் இணைக்கப்படுகிறது | फिर से जुड़ रहा है | ☐ |
| `p.invalid` | This link is not valid. Open the link from the laptop again. | இந்த இணைப்பு செல்லாது. மடிக்கணினியிலிருந்து இணைப்பை மீண்டும் திறக்கவும். | यह लिंक मान्य नहीं है। लैपटॉप से लिंक फिर से खोलें। | ☐ |
| `p.empty` | No alerts yet. This page lights up when a delivery needs you. | இன்னும் அறிவிப்புகள் இல்லை. ஒரு சரக்கு வருகைக்கு உங்கள் முடிவு தேவைப்படும்போது இந்தப் பக்கத்தில் தெரியும். | अभी कोई सूचना नहीं है। जब किसी माल पर आपके निर्णय की ज़रूरत होगी, तब यह पेज यहाँ दिखाएगा। | ☐ |
| `p.allow` | Allow notifications on this phone | இந்த தொலைபேசியில் அறிவிப்புகளை அனுமதிக்கவும் | इस फ़ोन पर सूचनाओं की अनुमति दें | ☐ |
| `p.count_title` | Count a delivery | சரக்கை எண்ணவும் | माल गिनें | ☐ |
| `p.count_hint` | Take a photo of the goods. The laptop counts them and the result appears below. | சரக்கின் புகைப்படம் எடுக்கவும். மடிக்கணினி அவற்றை எண்ணும்; முடிவு கீழே தெரியும். | माल की फ़ोटो लें। लैपटॉप उन्हें गिनेगा और नतीजा नीचे दिखेगा। | ☐ |
| `p.word_label` | What to count (a word such as box) | எதை எண்ண வேண்டும் (எ.கா. box) | क्या गिनना है (जैसे box) | ☐ |
| `p.take` | Take dock photo | புகைப்படம் எடுக்கவும் | फ़ोटो लें | ☐ |
| `p.sending` | Sending {kb} KB to the laptop | {kb} KB மடிக்கணினிக்கு அனுப்பப்படுகிறது | {kb} KB लैपटॉप को भेजा जा रहा है | ☐ |
| `p.received` | Received. Counting on the laptop. | பெறப்பட்டது. மடிக்கணினியில் எண்ணப்படுகிறது. | मिल गया। लैपटॉप पर गिनती हो रही है। | ☐ |
| `p.not_accepted` | Not accepted | ஏற்கப்படவில்லை | स्वीकार नहीं किया गया | ☐ |
| `p.unreachable` | Could not reach the laptop | மடிக்கணினியை அடைய முடியவில்லை | लैपटॉप तक नहीं पहुँचा जा सका | ☐ |
| `p.language` | Language | மொழி | भाषा | ☐ |
| `a.needs_owner.title` | {bill} needs you | {bill}: உங்கள் முடிவு தேவை | {bill}: आपके निर्णय की ज़रूरत है | ☐ |
| `a.needs_owner.body` | {cause}. {reason} | {cause}. {reason} | {cause}. {reason} | ☐ |
| `a.injection.title` | {bill}: hidden text tried to change the bank account | {bill}: மறைக்கப்பட்ட உரை வங்கிக் கணக்கை மாற்ற முயன்றது | {bill}: छिपे हुए टेक्स्ट ने बैंक खाता बदलने की कोशिश की | ☐ |
| `a.injection.body` | Ignored. Payment details come only from the supplier master. | புறக்கணிக்கப்பட்டது. பணம் செலுத்தும் விவரங்கள் சப்ளையரின் முதன்மைப் பதிவிலிருந்து மட்டுமே எடுக்கப்படும். | अनदेखा किया गया। भुगतान का विवरण केवल सप्लायर के मास्टर रिकॉर्ड से लिया जाता है। | ☐ |
| `a.readback.title` | {bill} readback failed | {bill}: பதிவை மீண்டும் சரிபார்த்தல் தோல்வியடைந்தது | {bill}: बही में दर्ज बिल की दोबारा जाँच विफल रही | ☐ |
| `a.readback.body` | {differences} | {differences} | {differences} | ☐ |
| `a.offline.title` | {bill} held, offline | {bill}: நிறுத்தி வைக்கப்பட்டது, இணையம் இல்லை | {bill}: रोका गया, नेटवर्क बंद है | ☐ |
| `a.offline.body` | The network is down. Nothing was entered or sent. | நெட்வொர்க் துண்டிக்கப்பட்டுள்ளது. எதுவும் பதிவு செய்யப்படவில்லை, அனுப்பப்படவும் இல்லை. | नेटवर्क बंद है। कुछ भी दर्ज या भेजा नहीं गया। | ☐ |
| `a.photo_received.title` | Dock photo received | புகைப்படம் பெறப்பட்டது | फ़ोटो मिल गई | ☐ |
| `a.photo_received.body` | {name}, {kb} KB. Counting {word}. | {name}, {kb} KB. {word} எண்ணப்படுகிறது. | {name}, {kb} KB। {word} गिना जा रहा है। | ☐ |
| `a.photo_saved.title` | Photo saved, not counted | புகைப்படம் சேமிக்கப்பட்டது, எண்ணப்படவில்லை | फ़ोटो सहेजी गई, गिनती नहीं हुई | ☐ |
| `a.photo_saved.body` | Start the app with --counter live to count photos. | புகைப்படங்களை எண்ண, செயலியை --counter live உடன் தொடங்கவும். | फ़ोटो गिनने के लिए ऐप को --counter live के साथ शुरू करें। | ☐ |
| `a.counted.title` | Counted {n} {word} | {n} {word} எண்ணப்பட்டது | {n} {word} गिने गए | ☐ |
| `a.counted.body` | {name} in {s} s on this laptop. | {name}: இந்த மடிக்கணினியில் {s} வினாடிகளில். | {name}: इस लैपटॉप पर {s} सेकंड में। | ☐ |
| `a.count_failed.title` | Count failed | எண்ணுதல் தோல்வியடைந்தது | गिनती विफल रही | ☐ |
| `a.count_failed.body` | {name}: {error} | {name}: {error} | {name}: {error} | ☐ |
| `a.dock_detected.title` | Delivery detected on the dock | சரக்கு வருகை கண்டறியப்பட்டது | माल की आमद का पता चला | ☐ |
| `a.dock_detected.body` | Movement at {at} s, {lag} s after it began. | {at} வினாடியில் அசைவு, தொடங்கிய {lag} வினாடிக்குப் பிறகு. | {at} सेकंड पर हलचल, शुरू होने के {lag} सेकंड बाद। | ☐ |
| `a.dock_complete.title` | Delivery complete | சரக்கு வருகை முடிந்தது | माल की आमद पूरी हुई | ☐ |
| `a.dock_complete.body` | {n} steady views saved from {start} s to {end} s. | {start} முதல் {end} வினாடி வரை {n} நிலையான காட்சிகள் சேமிக்கப்பட்டன. | {start} से {end} सेकंड तक {n} स्थिर दृश्य सहेजे गए। | ☐ |
| `a.dock_counted.title` | Counted {total} {word} on the dock | {total} {word} எண்ணப்பட்டது | {total} {word} गिने गए | ☐ |
| `a.dock_counted.body` | Match it against the bill before paying. | பணம் செலுத்தும் முன் பில்லுடன் ஒப்பிடவும். | भुगतान से पहले इसे बिल से मिलाएँ। | ☐ |
| `d.short_delivery` | Short delivery | குறைவான சரக்கு வருகை | कम माल आया | ☐ |
| `d.duplicate_bill` | Duplicate bill | நகல் பில் | दोहराया हुआ बिल | ☐ |
| `d.price_above_order` | Price above the order | ஆர்டரை விட அதிக விலை | ऑर्डर से ऊँची कीमत | ☐ |
| `d.count_unreliable` | The two counts disagree | இரண்டு எண்ணிக்கைகளும் ஒத்துப்போகவில்லை | दोनों गिनतियाँ मेल नहीं खातीं | ☐ |
| `d.unclear` | Unclear | தெளிவில்லை | स्पष्ट नहीं | ☐ |
| `u.skip` | Skip to content | உள்ளடக்கத்திற்குச் செல்லவும் | सामग्री पर जाएँ | ☐ |
| `u.sub` | Autonomous accounts payable that checks the goods, not just the paperwork | காகிதங்களை மட்டுமல்ல, சரக்கையும் சரிபார்க்கும் தானியங்கி செலுத்த வேண்டிய கணக்குகள் | ऑटोमैटिक भुगतान-लेखा, जो सिर्फ़ कागज़ नहीं, माल भी जाँचता है | ☐ |
| `u.nav.today` | Today | இன்று | आज | ☐ |
| `u.nav.approvals` | Approvals | ஒப்புதல்கள் | मंज़ूरियाँ | ☐ |
| `u.nav.boundary` | Boundary | எல்லை | सीमा | ☐ |
| `u.nav.benchmark` | Benchmark | ஒப்பீட்டுச் சோதனை | बेंचमार्क | ☐ |
| `u.net.cut` | Cut network | நெட்வொர்க்கைத் துண்டிக்கவும் | नेटवर्क काटें | ☐ |
| `u.net.reconnect` | Reconnect | மீண்டும் இணைக்கவும் | फिर से जोड़ें | ☐ |
| `u.net.on` | Network on | நெட்வொர்க் இயக்கத்தில் | नेटवर्क चालू | ☐ |
| `u.net.off` | Network cut | நெட்வொர்க் துண்டிக்கப்பட்டது | नेटवर्क कटा है | ☐ |
| `u.theme.light` | Light | ஒளி | हल्का | ☐ |
| `u.theme.dark` | Dark | இருள் | गहरा | ☐ |
| `u.today.title` | Today | இன்று | आज | ☐ |
| `u.today.hint` | Agents read the bill, look at what actually arrived, investigate any gap with evidence, and pay only what the books and the goods both support. | முகவர்கள் பில்லைப் படிக்கின்றன, உண்மையில் வந்த சரக்கைப் பார்க்கின்றன, ஏதேனும் இடைவெளி இருந்தால் ஆதாரத்துடன் விசாரிக்கின்றன, கணக்குகளும் சரக்கும் இரண்டும் ஆதரிப்பதற்கு மட்டுமே பணம் செலுத்துகின்றன. | एजेंट बिल पढ़ते हैं, देखते हैं कि असल में क्या आया, किसी भी अंतर की जाँच सबूत के साथ करते हैं, और सिर्फ़ उतना भुगतान करते हैं जितना बही और माल दोनों से साबित हो। | ☐ |
| `u.start` | Run today's bills | இன்றைய பில்களை இயக்கவும் | आज के बिल चलाएँ | ☐ |
| `u.th.bill` | Bill | பில் | बिल | ☐ |
| `u.th.supplier` | Supplier | சப்ளையர் | सप्लायर | ☐ |
| `u.th.read` | Read | படித்தல் | पढ़ना | ☐ |
| `u.th.count` | Count | எண்ணுதல் | गिनती | ☐ |
| `u.th.match` | Match | பொருத்தம் | मिलान | ☐ |
| `u.th.investigate` | Investigate | விசாரணை | जाँच | ☐ |
| `u.th.enter` | Enter | பதிவு | दर्ज करना | ☐ |
| `u.th.check` | Check | சரிபார்ப்பு | पुनः जाँच | ☐ |
| `u.th.status` | Status | நிலை | स्थिति | ☐ |
| `u.rows.empty` | No bills yet. Run today's bills to start the agents. | இன்னும் பில்கள் இல்லை. முகவர்களைத் தொடங்க இன்றைய பில்களை இயக்கவும். | अभी कोई बिल नहीं है। एजेंट शुरू करने के लिए आज के बिल चलाएँ। | ☐ |
| `u.tile.entered` | Entered and checked | பதிவு செய்து சரிபார்க்கப்பட்டது | दर्ज और जाँचे गए | ☐ |
| `u.tile.held` | Held for the owner | உரிமையாளருக்காக நிறுத்தப்பட்டது | मालिक के लिए रोके गए | ☐ |
| `u.tile.offline` | Held, offline | நிறுத்தப்பட்டது, இணையம் இல்லை | रोके गए, ऑफ़लाइन | ☐ |
| `u.tile.disputes` | Disputes sent | அனுப்பப்பட்ட புகார்கள் | भेजे गए विवाद | ☐ |
| `u.auto.alone` | Runs alone | தானாகவே நடக்கும் | अपने आप चलता है | ☐ |
| `u.auto.approval` | Waits for the owner | உரிமையாளருக்காகக் காத்திருக்கும் | मालिक की प्रतीक्षा करता है | ☐ |
| `u.auto.never` | Never | ஒருபோதும் இல்லை | कभी नहीं | ☐ |
| `u.auto.limit` | Owner limit {amount} | உரிமையாளர் வரம்பு {amount} | मालिक की सीमा {amount} | ☐ |
| `u.step.waiting` | Waiting | காத்திருக்கிறது | प्रतीक्षा | ☐ |
| `u.step.running` | Working | நடைபெறுகிறது | चल रहा है | ☐ |
| `u.step.done` | Done | முடிந்தது | पूरा | ☐ |
| `u.step.held` | Held | நிறுத்தப்பட்டது | रोका गया | ☐ |
| `u.step.failed` | Failed | தோல்வி | विफल | ☐ |
| `u.step.skipped` | Skipped | தவிர்க்கப்பட்டது | छोड़ा गया | ☐ |
| `u.state.queued` | Queued | வரிசையில் | कतार में | ☐ |
| `u.state.matched` | Matched | பொருந்தியது | मिलान हुआ | ☐ |
| `u.state.entered_checked` | Entered and checked | பதிவு செய்து சரிபார்க்கப்பட்டது | दर्ज और जाँचा गया | ☐ |
| `u.state.held_for_owner` | Needs you | உங்கள் முடிவு தேவை | आपकी ज़रूरत है | ☐ |
| `u.state.held_offline` | Held, offline | நிறுத்தப்பட்டது, இணையம் இல்லை | रोका गया, ऑफ़लाइन | ☐ |
| `u.state.approved` | Approved | அங்கீகரிக்கப்பட்டது | मंज़ूर | ☐ |
| `u.state.dispute_sent` | Dispute sent | புகார் அனுப்பப்பட்டது | विवाद भेजा गया | ☐ |
| `u.state.closed_by_owner` | Closed by owner | உரிமையாளர் மூடினார் | मालिक ने बंद किया | ☐ |
| `u.state.readback_failed` | Readback failed | மறுசரிபார்ப்பு தோல்வி | दोबारा जाँच विफल | ☐ |
| `u.state.failed` | Stopped | நின்றது | रुका | ☐ |
| `u.action.send_dispute` | send a dispute to the supplier | சப்ளையருக்குப் புகார் அனுப்பவும் | सप्लायर को विवाद भेजें | ☐ |
| `u.action.enter_bill` | enter the bill | பில்லைப் பதிவு செய்யவும் | बिल दर्ज करें | ☐ |
| `u.action.reject_duplicate` | reject the duplicate bill | நகல் பில்லை நிராகரிக்கவும் | दोहराया हुआ बिल अस्वीकार करें | ☐ |
| `u.action.hold_for_recount` | hold for a person to recount | ஒருவர் மீண்டும் எண்ணும் வரை நிறுத்தி வைக்கவும் | किसी व्यक्ति के दोबारा गिनने तक रोकें | ☐ |
| `u.action.enter_bill_for_received_quantity` | enter the bill for the received quantity | பெறப்பட்ட அளவுக்கு பில்லைப் பதிவு செய்யவும் | प्राप्त मात्रा के लिए बिल दर्ज करें | ☐ |
| `u.level.run_alone` | runs alone | தானாகவே நடக்கும் | अपने आप चलता है | ☐ |
| `u.level.run_with_approval` | waits for the owner | உரிமையாளருக்காகக் காத்திருக்கும் | मालिक की प्रतीक्षा करता है | ☐ |
| `u.level.never` | never | ஒருபோதும் இல்லை | कभी नहीं | ☐ |
| `u.appr.title` | Approvals | ஒப்புதல்கள் | मंज़ूरियाँ | ☐ |
| `u.appr.keys` | Keys: {j} {k} move, {a} approve, {r} reject | விசைகள்: {j} {k} நகர்த்த, {a} அங்கீகரிக்க, {r} நிராகரிக்க | कुंजियाँ: {j} {k} आगे-पीछे, {a} मंज़ूर करें, {r} अस्वीकार करें | ☐ |
| `u.appr.empty` | Nothing needs you right now. | இப்போது உங்கள் முடிவு தேவைப்படுவது எதுவும் இல்லை. | अभी किसी चीज़ पर आपके निर्णय की ज़रूरत नहीं है। | ☐ |
| `u.appr.proposes` | Agent proposes: {action}. Nothing has been entered. | முகவர் பரிந்துரைப்பது: {action}. எதுவும் பதிவு செய்யப்படவில்லை. | एजेंट का सुझाव: {action}। कुछ भी दर्ज नहीं किया गया है। | ☐ |
| `u.appr.statements` | {n} statements, each citing a record or photo. | {n} கூற்றுகள், ஒவ்வொன்றும் ஒரு பதிவு அல்லது புகைப்படத்தை ஆதாரமாகக் காட்டுகிறது. | {n} कथन, हर एक किसी रिकॉर्ड या फ़ोटो का हवाला देता है। | ☐ |
| `u.appr.open_inv` | Open the investigation | விசாரணையைத் திறக்கவும் | जाँच खोलें | ☐ |
| `u.btn.approve` | Approve (a) | அங்கீகரிக்கவும் (a) | मंज़ूर करें (a) | ☐ |
| `u.btn.reject` | Reject (r) | நிராகரிக்கவும் (r) | अस्वीकार करें (r) | ☐ |
| `u.btn.open_case` | Open case | வழக்கைத் திறக்கவும் | केस खोलें | ☐ |
| `u.btn.back` | Back to today | இன்றைக்குத் திரும்பவும் | आज पर वापस | ☐ |
| `u.case.investigation` | Investigation | விசாரணை | जाँच | ☐ |
| `u.case.proposes` | The agent proposes | முகவரின் பரிந்துரை | एजेंट का सुझाव | ☐ |
| `u.case.policy_says` | The policy says | கொள்கை கூறுவது | नीति के अनुसार | ☐ |
| `u.case.bill_seen` | The bill, as the model saw it | மாடல் பார்த்த பில் | बिल, जैसा मॉडल ने देखा | ☐ |
| `u.case.dock` | The dock | சரக்கு இறக்குமிடம் | माल उतरने की जगह | ☐ |
| `u.case.match` | Three way match, as a running total on the order | மூன்று வழி பொருத்தம், ஆர்டரின் தொடர் கூட்டுத்தொகையாக | तीन-तरफ़ा मिलान, ऑर्डर पर चलते कुल योग के रूप में | ☐ |
| `u.case.readback` | Ledger readback | கணக்கேட்டுப் பதிவின் மறுசரிபார்ப்பு | बही में दर्ज की दोबारा जाँच | ☐ |
| `u.case.dispute` | Dispute to the supplier | சப்ளையருக்கான புகார் | सप्लायर को विवाद | ☐ |
| `u.case.receipts` | Receipts | ரசீதுகள் | रसीदें | ☐ |
| `s.queued` | Queued | வரிசையில் | कतार में | ☐ |
| `s.reading_the_bill` | Reading the bill | பில் படிக்கப்படுகிறது | बिल पढ़ा जा रहा है | ☐ |
| `s.counting_the_delivery` | Counting the delivery | சரக்கு எண்ணப்படுகிறது | माल की गिनती हो रही है | ☐ |
| `s.matching` | Matching | பொருத்திப் பார்க்கப்படுகிறது | मिलान हो रहा है | ☐ |
| `s.waiting_for_the_owner` | Waiting for the owner | உரிமையாளருக்காகக் காத்திருக்கிறது | मालिक की प्रतीक्षा है | ☐ |
| `s.investigating` | Investigating | விசாரிக்கப்படுகிறது | जाँच हो रही है | ☐ |
| `s.entering_the_bill` | Entering the bill | பில் பதிவு செய்யப்படுகிறது | बिल दर्ज हो रहा है | ☐ |
| `s.checking_the_ledger` | Checking the ledger | கணக்கேடு சரிபார்க்கப்படுகிறது | बही की जाँच हो रही है | ☐ |
| `s.readback_failed_not_treated_as_entered` | Readback failed: not treated as entered | மறுசரிபார்ப்பு தோல்வி: பதிவு செய்ததாகக் கருதப்படவில்லை | दोबारा जाँच विफल: दर्ज नहीं माना गया | ☐ |
| `s.entered_and_checked` | Entered and checked | பதிவு செய்து சரிபார்க்கப்பட்டது | दर्ज और जाँचा गया | ☐ |
| `s.held_offline` | Held, offline | நிறுத்தப்பட்டது, இணையம் இல்லை | रोका गया, ऑफ़लाइन | ☐ |
| `s.rejected_by_the_owner_nothing_entered_or_sent` | Rejected by the owner: nothing entered or sent | உரிமையாளர் நிராகரித்தார்: எதுவும் பதிவு செய்யப்படவில்லை, அனுப்பப்படவும் இல்லை | मालिक ने अस्वीकार किया: कुछ भी दर्ज या भेजा नहीं गया | ☐ |
| `s.duplicate_bill_rejected_nothing_entered` | Duplicate bill rejected: nothing entered | நகல் பில் நிராகரிக்கப்பட்டது: எதுவும் பதிவு செய்யப்படவில்லை | दोहराया हुआ बिल अस्वीकार: कुछ भी दर्ज नहीं हुआ | ☐ |
| `s.sending_the_dispute` | Sending the dispute | புகார் அனுப்பப்படுகிறது | विवाद भेजा जा रहा है | ☐ |
| `s.dispute_sent_to_the_supplier_bill_not_entered` | Dispute sent to the supplier; bill not entered | சப்ளையருக்குப் புகார் அனுப்பப்பட்டது; பில் பதிவு செய்யப்படவில்லை | सप्लायर को विवाद भेजा गया; बिल दर्ज नहीं हुआ | ☐ |
| `u.details_english` | Details below come from the bill, the model and the matcher and stay in English. | கீழுள்ள விவரங்கள் பில், மாடல் மற்றும் பொருத்தும் நிரலிலிருந்து வருகின்றன; அவை ஆங்கிலத்திலேயே இருக்கும். | नीचे का विवरण बिल, मॉडल और मिलान प्रोग्राम से आता है और अंग्रेज़ी में ही रहता है। | ☐ |
