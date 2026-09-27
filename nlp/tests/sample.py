"""نمونه طلایی پیام غیرصریح با درصد و نقل‌قول."""

SAMPLE_TEXT = """
دیروز رفتم واحد مالی گفت :
به دلیل کمبود نیروی متخصص ۳۰ درصد کاهش عملکرد داریم که البته ۱۰ درصد آن مربوط به واحد بازاریابی است نه صرفا نبود نیروی متخصص
""".strip()

GOLD_FACTS = {
    "facts": [
        {
            "id": "q1",
            "kind": "quantity",
            "name": "کاهش عملکرد",
            "value": 30,
            "unit": "percent",
            "role": "total",
            "grounding": "explicit",
            "mention_text": "30 درصد کاهش عملکرد",
            "confidence": 0.95,
        },
        {
            "id": "q2",
            "kind": "quantity",
            "name": "سهم بازاریابی",
            "value": 10,
            "unit": "percent",
            "role": "part",
            "grounding": "explicit",
            "mention_text": "10 درصد آن مربوط به واحد بازاریابی",
            "confidence": 0.95,
        },
        {
            "id": "q3",
            "kind": "quantity",
            "name": "سهم کمبود نیروی متخصص",
            "value": 20,
            "unit": "percent",
            "role": "remainder",
            "grounding": "derived",
            "derivation": "subtract",
            "source_ids": ["q1", "q2"],
            "mention_text": "کمبود نیروی متخصص",
            "evidence_texts": [
                "30 درصد کاهش عملکرد",
                "10 درصد آن مربوط به واحد بازاریابی",
            ],
            "confidence": 0.9,
        },
        {
            "id": "c1",
            "kind": "cause",
            "name": "کمبود نیروی متخصص",
            "effect": "کاهش عملکرد",
            "grounding": "explicit",
            "mention_text": "کمبود نیروی متخصص",
            "confidence": 0.9,
        },
        {
            "id": "c2",
            "kind": "cause",
            "name": "واحد بازاریابی",
            "effect": "کاهش عملکرد",
            "grounding": "explicit",
            "mention_text": "واحد بازاریابی",
            "confidence": 0.85,
        },
    ]
}

GOLD_QUOTES = {
    "quotes": [
        {
            "mode": "indirect",
            "attributed_to": "واحد مالی",
            "quoted_text": "به دلیل کمبود نیروی متخصص 30 درصد کاهش عملکرد داریم",
            "mention_text": "گفت",
            "confidence": 0.9,
        }
    ]
}

GOLD_FRAME = {
    "frame": {
        "title": "کاهش عملکرد واحد مالی",
        "unit": "واحد مالی",
        "process": "staffing",
        "scope": "organizational",
        "about": "کمبود نیروی متخصص",
        "confidence": 0.8,
    }
}
