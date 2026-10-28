"""A complete, honest fallback: the same hand-written lesson in three languages.

These are teaching materials, not synthetic answers to arbitrary user topics.
"""

SAMPLES = {
    "en": {
        "title": "How does a Python loop work?",
        "scenes": [
            {
                "type": "title_card",
                "heading": "How does a Python loop work?",
                "narration": "A loop lets Python repeat an action, one item at a time. Let's look at a simple example together.",
                "code": "for i in range(3):\n    print(i)",
                "items": ["0", "1", "2"],
            },
            {
                "type": "code_walkthrough",
                "heading": "First, read the loop",
                "narration": "Here, range of three gives us the numbers zero, one, and two. The loop takes one number at a time.",
                "code": "for i in range(3):\n    print(i)",
                "highlight_lines": [1],
            },
            {
                "type": "diagram",
                "heading": "One value at a time",
                "narration": "On each pass, i takes the next value. Then Python runs the indented print instruction.",
                "items": ["i = 0", "i = 1", "i = 2"],
            },
            {
                "type": "code_walkthrough",
                "heading": "See what happens",
                "narration": "The result is zero, one, two. When there are no more values, the loop stops. That's a loop!",
                "code": "0\n1\n2",
                "highlight_lines": [1, 2, 3],
            },
        ],
    },
    "hi": {
        "title": "Python लूप कैसे काम करता है?",
        "scenes": [
            {
                "type": "title_card",
                "heading": "Python लूप कैसे काम करता है?",
                "narration": "लूप की मदद से Python किसी काम को बार बार कर सकता है। चलिए एक आसान उदाहरण देखते हैं।",
                "code": "for i in range(3):\n    print(i)",
                "items": ["0", "1", "2"],
            },
            {
                "type": "code_walkthrough",
                "heading": "पहले कोड पढ़ें",
                "narration": "यहाँ range तीन हमें शून्य, एक और दो देता है। लूप एक बार में एक संख्या उठाता है।",
                "code": "for i in range(3):\n    print(i)",
                "highlight_lines": [1],
            },
            {
                "type": "diagram",
                "heading": "एक बार में एक मान",
                "narration": "हर बार i अगला मान लेता है। फिर Python अंदर लिखे print निर्देश को चलाता है।",
                "items": ["i = 0", "i = 1", "i = 2"],
            },
            {
                "type": "code_walkthrough",
                "heading": "नतीजा देखें",
                "narration": "नतीजा है शून्य, एक, दो। जब कोई मान नहीं बचता, लूप रुक जाता है। यही है लूप!",
                "code": "0\n1\n2",
                "highlight_lines": [1, 2, 3],
            },
        ],
    },
    "ta": {
        "title": "Python லூப் எப்படி வேலை செய்கிறது?",
        "scenes": [
            {
                "type": "title_card",
                "heading": "Python லூப் எப்படி வேலை செய்கிறது?",
                "narration": "ஒரு செயலை மீண்டும் மீண்டும் செய்ய Python லூப் உதவுகிறது. ஒரு எளிய எடுத்துக்காட்டைப் பார்ப்போம்.",
                "code": "for i in range(3):\n    print(i)",
                "items": ["0", "1", "2"],
            },
            {
                "type": "code_walkthrough",
                "heading": "முதலில் குறியீட்டைப் படிப்போம்",
                "narration": "இங்கு range மூன்று என்பது பூஜ்ஜியம், ஒன்று, இரண்டு ஆகிய எண்களைத் தருகிறது. லூப் ஒரு நேரத்தில் ஒரு எண்ணை எடுக்கும்.",
                "code": "for i in range(3):\n    print(i)",
                "highlight_lines": [1],
            },
            {
                "type": "diagram",
                "heading": "ஒரு நேரத்தில் ஒரு மதிப்பு",
                "narration": "ஒவ்வொரு சுற்றிலும் i அடுத்த மதிப்பை எடுக்கிறது. பிறகு உள்ளே இருக்கும் print கட்டளையை Python இயக்குகிறது.",
                "items": ["i = 0", "i = 1", "i = 2"],
            },
            {
                "type": "code_walkthrough",
                "heading": "முடிவைப் பார்ப்போம்",
                "narration": "முடிவு பூஜ்ஜியம், ஒன்று, இரண்டு. அடுத்து மதிப்புகள் இல்லாதபோது லூப் நின்றுவிடும். இதுவே லூப்!",
                "code": "0\n1\n2",
                "highlight_lines": [1, 2, 3],
            },
        ],
    },
}

# A second honest offline fallback for the common linked-list request. These
# examples deliberately teach a singly linked list, not arbitrary variations.
LINKED_SAMPLES = {
    'en': {
        'title': 'How does a linked list work?',
        'scenes': [
            {'type': 'title_card', 'heading': 'A chain of linked nodes',
             'narration': 'A linked list is a chain of nodes. Each node stores a value and a reference to the next node.',
             'items': ['10', '20', '∅']},
            {'type': 'diagram', 'heading': 'Follow the links', 'items': ['head', '10 | next', '20 | next', 'None'],
             'narration': 'The head points to the first node, which stores ten. Its next link points to the node holding twenty. The final link is None, so the chain ends.'},
            {'type': 'code_walkthrough', 'heading': 'Build a tiny list',
             'code': 'head = {"value": 10, "next": None}\nhead["next"] = {"value": 20,\n                "next": None}',
             'highlight_lines': [1, 2, 3],
             'narration': 'Here we create a node containing ten, then attach a second node containing twenty. Its next link is None, so it is last.'},
            {'type': 'code_walkthrough', 'heading': 'Walk through the list',
             'code': 'current = head\nwhile current is not None:\n    print(current["value"])\n    current = current["next"]',
             'highlight_lines': [1, 2, 3, 4],
             'narration': 'Begin at head. While current is not None, print its value and follow its next link. This visits ten, then twenty, and stops.'},
            {'type': 'title_card', 'heading': 'The trade-off',
             'narration': 'Finding an item can require following many links. Adding a new first node is quick, but each link uses extra memory.',
             'items': ['head', 'link', 'end']},
        ],
    },
    'hi': {
        'title': 'लिंक्ड लिस्ट कैसे काम करती है?',
        'scenes': [
            {'type': 'title_card', 'heading': 'जुड़े हुए नोड्स की श्रृंखला',
             'narration': 'लिंक्ड लिस्ट नोड्स की एक श्रृंखला है। हर नोड में एक मान और अगले नोड का संदर्भ होता है।',
             'items': ['10', '20', '∅']},
            {'type': 'diagram', 'heading': 'लिंक्स को समझें', 'items': ['हेड', '10 | लिंक', '20 | लिंक', 'अंत'],
             'narration': 'हेड पहले नोड को दिखाता है, जिसका मान दस है। उसका लिंक बीस वाले नोड को दिखाता है। अंतिम लिंक खाली है, इसलिए श्रृंखला समाप्त होती है।'},
            {'type': 'code_walkthrough', 'heading': 'एक छोटी लिस्ट बनाएँ',
             'code': 'head = {"value": 10, "next": None}\nhead["next"] = {"value": 20,\n                "next": None}',
             'highlight_lines': [1, 2, 3],
             'narration': 'हम दस वाला नोड बनाते हैं और उससे बीस वाला दूसरा नोड जोड़ते हैं। उसका अगला लिंक खाली है, इसलिए वह आखिरी है।'},
            {'type': 'code_walkthrough', 'heading': 'लिस्ट में आगे बढ़ें',
             'code': 'current = head\nwhile current is not None:\n    print(current["value"])\n    current = current["next"]',
             'highlight_lines': [1, 2, 3, 4],
             'narration': 'हेड से शुरू करें। जब तक नोड खाली न हो, उसका मान दिखाएँ और अगले लिंक पर जाएँ। पहले दस, फिर बीस दिखेगा, और लूप रुकेगा।'},
            {'type': 'title_card', 'heading': 'इसके फायदे और सीमाएँ',
             'narration': 'कोई मान खोजने में कई लिंक्स से गुजरना पड़ सकता है। शुरुआत में नया नोड जल्दी जोड़ा जा सकता है, लेकिन लिंक्स अतिरिक्त मेमोरी लेते हैं।',
             'items': ['हेड', 'लिंक', 'अंत']},
        ],
    },
    'ta': {
        'title': 'இணைப்புப் பட்டியல் எப்படி வேலை செய்கிறது?',
        'scenes': [
            {'type': 'title_card', 'heading': 'இணைக்கப்பட்ட முனைகளின் சங்கிலி',
             'narration': 'இணைப்புப் பட்டியல் என்பது முனைகளின் சங்கிலி. ஒவ்வொரு முனையிலும் ஒரு மதிப்பும் அடுத்த முனைக்கான இணைப்பும் இருக்கும்.',
             'items': ['10', '20', '∅']},
            {'type': 'diagram', 'heading': 'இணைப்புகளைப் பின்தொடர்வோம்', 'items': ['தலை', '10 | அடுத்து', '20 | அடுத்து', 'முடிவு'],
             'narration': 'தலை முதல் முனையைக் காட்டுகிறது. அதில் பத்து உள்ளது. அதன் இணைப்பு இருபது உள்ள முனையைக் காட்டுகிறது. கடைசி இணைப்பு காலியாக இருப்பதால் சங்கிலி முடிகிறது.'},
            {'type': 'code_walkthrough', 'heading': 'ஒரு சிறிய பட்டியலை உருவாக்குவோம்',
             'code': 'head = {"value": 10, "next": None}\nhead["next"] = {"value": 20,\n                "next": None}',
             'highlight_lines': [1, 2, 3],
             'narration': 'முதலில் பத்து உள்ள முனையை உருவாக்குகிறோம். அடுத்து இருபது உள்ள முனையை இணைக்கிறோம். அதன் அடுத்த இணைப்பு காலி, அதனால் அது கடைசி முனை.'},
            {'type': 'code_walkthrough', 'heading': 'பட்டியலைக் கடந்து செல்வோம்',
             'code': 'current = head\nwhile current is not None:\n    print(current["value"])\n    current = current["next"]',
             'highlight_lines': [1, 2, 3, 4],
             'narration': 'தலையில் தொடங்குங்கள். முனை காலியாக இல்லாத வரை அதன் மதிப்பைக் காட்டி அடுத்த இணைப்புக்குச் செல்லுங்கள். பத்து, பிறகு இருபது காட்டப்பட்டு லூப் நிற்கும்.'},
            {'type': 'title_card', 'heading': 'நன்மையும் வரம்பும்',
             'narration': 'ஒரு மதிப்பைத் தேடப் பல இணைப்புகளைக் கடக்க வேண்டியிருக்கும். தொடக்கத்தில் முனையை விரைவாகச் சேர்க்கலாம், ஆனால் இணைப்புகளுக்குக் கூடுதல் நினைவகம் தேவை.',
             'items': ['தலை', 'இணைப்பு', 'முடிவு']},
        ],
    },
}
