import re
from typing import Dict
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.text_rank import TextRankSummarizer

try:
    import nltk
    nltk.download('punkt', quiet=True)
except Exception:
    pass

DATE_PAT = re.compile(r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s?\d{1,2}\b", re.I)
KEYWORDS_CRITICAL = [
    "deadline", "register", "registration", "apply", "application",
    "today", "tomorrow", "closes", "limited spots", "RSVP", "now open",
]
KEYWORDS_TIMED = ["event", "workshop", "seminar", "webinar", "meeting", "tonight", "this week"]

def summarize_text(caption: str, max_sentences: int = 3) -> str:
    caption = caption.strip()
    if not caption:
        return "(No caption)"
    parser = PlaintextParser.from_string(caption, Tokenizer("english"))
    summarizer = TextRankSummarizer()
    sentences = summarizer(parser.document, max_sentences)
    text = " ".join(str(s) for s in sentences).strip()
    return text if len(text) > 0 else caption[:280]

def classify_importance(caption: str) -> str:
    low = caption.lower()
    if any(k in low for k in KEYWORDS_CRITICAL):
        return "Critical"
    if any(k in low for k in KEYWORDS_TIMED) or DATE_PAT.search(caption):
        return "Time-Sensitive"
    return "FYI"

def extract_date_hint(caption: str) -> str:
    m = DATE_PAT.search(caption)
    return m.group(0) if m else ""

def analyze_item(item: Dict) -> Dict:
    cap = item.get("caption", "")
    return {
        **item,
        "summary": summarize_text(cap, max_sentences=3),
        "importance": classify_importance(cap),
        "date_hint": extract_date_hint(cap),
    }
