"""
Image Text -> Claim Evidence for TrustLens.

Takes the text already extracted by the Phase 4 OCR (`OcrResult`; no second OCR
engine) and compares it with the user's claim, fact by fact.

Flow:
    OcrResult -> clean text -> split sentences -> extract claim points
    (entities, terms/actions, numbers, dates, locations) -> find them in the image
    text -> classify: SUPPORTS / CONTRADICTS / PARTIALLY_SUPPORTS / UNRELATED /
    INSUFFICIENT_TEXT -> concise explanation.

EPISTEMIC RULE: the text in an image is evidence about what the image *states*.
It is never treated as proof that the statement is true. The explanation is always
worded as "the image contains text stating X, which supports/contradicts the claim".

The comparison is deterministic and rule-based (no LLM), so results are reproducible
and explainable.
"""
import difflib
import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any, List, Optional, Set, Tuple

from backend.schemas.image_analysis import OcrResult
from backend.schemas.investigation import ImageTextEvidence

# ----------------------------------------------------------------------------
# Tunables
# ----------------------------------------------------------------------------
MIN_OCR_QUALITY = 0.50          # below this the OCR is too poor to compare
MIN_MEANINGFUL_TOKENS = 2       # fewer meaningful words than this -> insufficient
MIN_CLEAN_RATIO = 0.50          # share of OCR tokens that survive noise cleaning
MAX_EXTRACTED_CHARS = 2000
FUZZY_CUTOFF = 0.84             # tolerance for OCR character errors in long words

MONTHS = {
    "january": 1, "jan": 1, "february": 2, "feb": 2, "march": 3, "mar": 3,
    "april": 4, "apr": 4, "may": 5, "june": 6, "jun": 6, "july": 7, "jul": 7,
    "august": 8, "aug": 8, "september": 9, "sept": 9, "sep": 9, "october": 10,
    "oct": 10, "november": 11, "nov": 11, "december": 12, "dec": 12,
}
# "May" must be capitalised to count as a month (it is also a common verb).
_MONTH_RE = (
    r"(?:(?i:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|june?|july?|aug(?:ust)?|"
    r"sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)|May)"
)

STOPWORDS = set("""
a an the and or but of in on at to for from with by as is are was were be been being has have had do does did
that this these those it its into over after before about up down out new says said say also will would can could
may might shall should not no yes than then there their they them he she his her we our you your i who whom which
what when where why how all any each more most other some such only own same so too very just if
""".split())

CURRENCY_WORDS = {"rs", "inr", "usd", "rupees", "rupee", "dollars", "dollar", "eur", "euro", "euros"}

DENIAL_RE = re.compile(
    r"\b(fake|false|hoax|rumou?rs?|misleading|debunked|fact[- ]?check(?:ed)?|denies|denied|deny|"
    r"not true|no such|baseless|fabricated|untrue)\b",
    re.IGNORECASE,
)

# Known places: used so a location *contradiction* is only declared between two
# recognisable places (e.g. Delhi vs Mumbai), never between arbitrary capitalised words.
GAZETTEER = {n.strip() for n in """
delhi, new delhi, mumbai, bombay, kolkata, calcutta, chennai, madras, bengaluru, bangalore, hyderabad, pune,
ahmedabad, jaipur, lucknow, kanpur, nagpur, indore, bhopal, patna, ranchi, raipur, surat, vadodara, chandigarh,
amritsar, ludhiana, srinagar, shimla, dehradun, guwahati, shillong, imphal, kohima, aizawl, agartala, itanagar,
gangtok, bhubaneswar, visakhapatnam, vijayawada, coimbatore, madurai, kochi, cochin, thiruvananthapuram,
trivandrum, mysuru, mysore, mangaluru, panaji, goa, noida, gurugram, gurgaon, ghaziabad, faridabad, varanasi,
prayagraj, allahabad, agra, meerut, andhra pradesh, arunachal pradesh, assam, bihar, chhattisgarh, gujarat,
haryana, himachal pradesh, jharkhand, karnataka, kerala, madhya pradesh, maharashtra, manipur, meghalaya,
mizoram, nagaland, odisha, punjab, rajasthan, sikkim, tamil nadu, telangana, tripura, uttar pradesh,
uttarakhand, west bengal, kashmir, ladakh, india, pakistan, china, nepal, bangladesh, sri lanka, bhutan,
afghanistan, russia, ukraine, usa, united states, america, canada, mexico, brazil, argentina, uk,
united kingdom, england, scotland, ireland, france, germany, italy, spain, japan, north korea, south korea,
australia, new zealand, israel, gaza, iran, iraq, saudi arabia, turkey, egypt, nigeria, kenya, south africa,
dubai, london, paris, berlin, moscow, washington, new york, beijing, tokyo, singapore
""".replace("\n", " ").split(",") if n.strip()}
LOCATION_ALIASES = {
    "bombay": "mumbai", "calcutta": "kolkata", "madras": "chennai", "bangalore": "bengaluru",
    "cochin": "kochi", "trivandrum": "thiruvananthapuram", "mysore": "mysuru", "gurgaon": "gurugram",
    "allahabad": "prayagraj", "new delhi": "delhi", "america": "united states", "usa": "united states",
    "uk": "united kingdom",
}
_LOC_PREP_RE = re.compile(
    r"\b(?:[Ii]n|[Aa]t|[Nn]ear|[Aa]cross|[Ff]rom|[Ii]nside|[Oo]utside)\s+"
    r"((?:[A-Z][\w'’-]*)(?:\s+[A-Z][\w'’-]*){0,2})"
)


# ----------------------------------------------------------------------------
# Data holders
# ----------------------------------------------------------------------------
@dataclass
class _Point:
    kind: str                 # entity | term | number | date | location
    display: str
    data: Any = None
    status: str = "missing"   # matched | contradicted | missing
    detail: str = ""


@dataclass
class _Facts:
    dates: List[Tuple[Optional[int], Optional[int], Optional[int], str]] = field(default_factory=list)
    numbers: List[Tuple[float, str, str]] = field(default_factory=list)   # value, kind, raw
    locations: List[Tuple[str, str]] = field(default_factory=list)        # canonical, raw


# ----------------------------------------------------------------------------
# Cleaning / tokenising
# ----------------------------------------------------------------------------
def clean_ocr_text(raw: str) -> Tuple[str, float]:
    """
    Normalise OCR output and drop obvious noise tokens.
    Returns (clean_text, kept_ratio) where kept_ratio = surviving tokens / original tokens.
    """
    if not raw:
        return "", 0.0
    t = unicodedata.normalize("NFKC", raw)
    t = re.sub(r"[\u200b-\u200f\ufeff]", "", t)
    t = t.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    t = re.sub(r"[|_~^\\]+", " ", t)           # table-border / scan artefacts
    tokens = t.split()
    kept: List[str] = []
    for tok in tokens:
        if not re.search(r"[A-Za-z0-9\u20b9$€£%\u0900-\u097F]", tok):
            continue                                   # pure punctuation
        core = re.sub(r"[^A-Za-z0-9]", "", tok)
        if len(core) == 1 and not core.isdigit() and core not in ("a", "A", "I") and not core.isupper():
            continue                                   # stray single lowercase letter
        kept.append(tok)
    ratio = len(kept) / len(tokens) if tokens else 0.0
    return " ".join(kept), round(ratio, 3)


def _sentences(text: str) -> List[str]:
    protected = re.sub(r"\b(Rs|Dr|Mr|Mrs|Ms|St|No|vs|Govt|Gov|Min|Co|Ltd)\.", r"\1", text)
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'\u20b9])", protected)
    return [p.strip() for p in parts if p.strip()]


def _words(text: str) -> List[str]:
    return re.findall(r"[^\W\d_]+|\d+", text.lower())


def _stem(w: str) -> str:
    w = w.lower()
    for suf in ("ations", "ation", "ments", "ment", "ings", "ing", "ied", "ies", "ed", "es", "s", "e", "ly"):
        if w.endswith(suf) and len(w) - len(suf) >= 4:
            return w[: -len(suf)]
    return w


def _tok_eq(a: str, b: str) -> bool:
    """Exact match, or fuzzy match for longer words (tolerates OCR character errors)."""
    if a == b:
        return True
    if min(len(a), len(b)) < 5:
        return False
    return difflib.SequenceMatcher(None, a, b).ratio() >= FUZZY_CUTOFF


# ----------------------------------------------------------------------------
# Fact extraction (dates, numbers, locations)
# ----------------------------------------------------------------------------
def _month_num(tok: str) -> int:
    return MONTHS[tok.lower().rstrip(".")]


def _extract_dates(text: str) -> Tuple[List[Tuple[Optional[int], Optional[int], Optional[int], str]], str]:
    """Return (dates, text_with_dates_masked)."""
    dates: List[Tuple[Optional[int], Optional[int], Optional[int], str]] = []
    work = text
    patterns = [
        # 10 March 2027 / 10th of March
        (rf"(?P<d>\d{{1,2}})(?:st|nd|rd|th)?\s+(?:of\s+)?(?P<m>{_MONTH_RE})\b\.?,?(?:\s*(?P<y>(?:19|20)\d{{2}}))?", "dmy"),
        # March 10, 2027
        (rf"(?P<m>{_MONTH_RE})\b\.?\s+(?P<d>\d{{1,2}})(?:st|nd|rd|th)?(?!\d)(?:,?\s*(?P<y>(?:19|20)\d{{2}}))?", "mdy"),
        # March 2027
        (rf"(?P<m>{_MONTH_RE})\b\.?,?\s+(?P<y>(?:19|20)\d{{2}})", "my"),
        # 10/03/2027 (day first)
        (r"(?P<d>\d{1,2})[/.\-](?P<m>\d{1,2})[/.\-](?P<y>(?:19|20)?\d{2})\b", "num"),
        # bare month
        (rf"\b(?P<m>{_MONTH_RE})\b", "m"),
        # bare year
        (r"(?<![\d.,])(?P<y>(?:19|20)\d{2})(?![\d])", "y"),
    ]
    for pat, kind in patterns:
        def repl(m: "re.Match") -> str:
            gd = m.groupdict()
            d = int(gd["d"]) if gd.get("d") else None
            mo: Optional[int] = None
            if gd.get("m"):
                mo = int(gd["m"]) if gd["m"].isdigit() else _month_num(gd["m"])
            y: Optional[int] = None
            if gd.get("y"):
                y = int(gd["y"])
                if y < 100:
                    y += 2000
            if (d is not None and not 1 <= d <= 31) or (mo is not None and not 1 <= mo <= 12):
                return m.group(0)       # not a real date; leave for number extraction
            dates.append((d, mo, y, m.group(0).strip(" ,.")))
            return " "
        work = re.sub(pat, repl, work)
    return dates, work


_NUM_RE = re.compile(
    r"(?P<cur>₹|rs\.?|inr|\$|usd|€|£)?\s?(?P<num>\d[\d,]*(?:\.\d+)?)"
    r"(?:\s?(?P<unit>%|per\s?cent|lakhs?|crores?|million|billion|thousand|k\b))?"
    r"(?:\s+(?P<tail>rupees?|rs|inr|dollars?|usd|euros?))?",
    re.IGNORECASE,
)
_UNIT_MULT = {"lakh": 1e5, "lakhs": 1e5, "crore": 1e7, "crores": 1e7, "million": 1e6,
              "billion": 1e9, "thousand": 1e3, "k": 1e3}


def _extract_numbers(text: str) -> List[Tuple[float, str, str]]:
    out: List[Tuple[float, str, str]] = []
    for m in _NUM_RE.finditer(text):
        try:
            value = float(m.group("num").replace(",", "").rstrip("."))
        except ValueError:
            continue
        unit = (m.group("unit") or "").lower().replace(" ", "")
        cur = m.group("cur")
        tail = m.group("tail")
        if unit in ("%", "percent"):
            kind = "percent"
        elif cur or tail or unit in ("lakh", "lakhs", "crore", "crores"):
            kind = "money"
        else:
            kind = "count"
        value *= _UNIT_MULT.get(unit, 1.0)
        out.append((value, kind, m.group(0).strip()))
    return out


def _canon_location(name: str) -> str:
    n = re.sub(r"[^a-z ]", "", name.lower()).strip()
    return LOCATION_ALIASES.get(n, n)


def _extract_locations(text: str) -> List[Tuple[str, str]]:
    found: List[Tuple[str, str]] = []
    seen: Set[str] = set()
    low = text.lower()
    # 1. gazetteer scan (case-insensitive, works for lowercase claims)
    for place in sorted(GAZETTEER, key=len, reverse=True):
        gm = re.search(rf"\b{re.escape(place)}\b", low)
        if gm:
            c = _canon_location(place)
            if c not in seen:
                seen.add(c)
                found.append((c, text[gm.start():gm.end()]))   # keep original casing
    # 2. "in/at/near <Capitalised Name>" slots (unknown places)
    for m in _LOC_PREP_RE.finditer(text):
        words: List[str] = []
        for w in m.group(1).split():
            if w.lower() in STOPWORDS or w.lower() in MONTHS:
                break
            words.append(w)
        if not words:
            continue
        raw = " ".join(words)
        c = _canon_location(raw)
        if c and c not in seen and not any(c in s2 or s2 in c for s2 in seen):
            seen.add(c)
            found.append((c, raw))
    return found


def _loc_eq(a: str, b: str) -> bool:
    return a == b or _tok_eq(a, b) or (a in b.split()) or (b in a.split())


def _extract_facts(text: str) -> _Facts:
    dates, masked = _extract_dates(text)
    return _Facts(dates=dates, numbers=_extract_numbers(masked), locations=_extract_locations(text))


# ----------------------------------------------------------------------------
# Claim points
# ----------------------------------------------------------------------------
def _claim_points(claim: str) -> List[_Point]:
    facts = _extract_facts(claim)
    points: List[_Point] = []
    covered_words: Set[str] = set()

    for canon, raw in facts.locations:
        points.append(_Point("location", raw, canon))
        covered_words.update(_words(raw))
    for d, m, y, raw in facts.dates:
        points.append(_Point("date", raw, (d, m, y)))
        covered_words.update(_words(raw))
    for value, kind, raw in facts.numbers:
        points.append(_Point("number", raw, (value, kind)))
        covered_words.update(_words(raw))

    # Entities: runs of Capitalised / single-letter-uppercase tokens
    loc_names = {c for c, _ in facts.locations}
    for m in re.finditer(r"\b[A-Z][\w.&'’-]*(?:\s+[A-Z0-9][\w.&'’-]*)*", claim):
        toks = [t.strip(".,;:!?\"'()") for t in m.group(0).split()]
        toks = [t for t in toks if t]
        while toks and toks[0].lower() in STOPWORDS:
            toks.pop(0)
        toks = [t for t in toks if t.lower() not in MONTHS]
        if not toks:
            continue
        phrase = " ".join(toks)
        if _canon_location(phrase) in loc_names or phrase.lower() in loc_names:
            continue
        words = [w.lower() for w in _words(phrase)]
        if not words:
            continue
        points.append(_Point("entity", phrase, words))
        covered_words.update(words)

    # Terms (actions / events / objects): remaining content words
    seen_stems: Set[str] = set()
    for w in _words(claim):
        if (w in STOPWORDS or w in MONTHS or w in CURRENCY_WORDS or w.isdigit() or len(w) < 3
                or w in covered_words):
            continue
        st = _stem(w)
        if st in seen_stems:
            continue
        seen_stems.add(st)
        points.append(_Point("term", w, st))
    return points


# ----------------------------------------------------------------------------
# Matching
# ----------------------------------------------------------------------------
def _phrase_in_tokens(phrase: List[str], toks: List[str]) -> bool:
    n = len(phrase)
    if n == 0 or len(toks) < n:
        return False
    for i in range(len(toks) - n + 1):
        if all(_tok_eq(phrase[j], toks[i + j]) for j in range(n)):
            return True
    return False


def _topical_match(point: _Point, text: str) -> bool:
    toks = _words(text)
    if point.kind == "entity":
        return _phrase_in_tokens(point.data, toks)
    if point.kind == "term":
        return any(_tok_eq(point.data, _stem(t)) for t in toks)
    return False


def _fmt_num(raw: str) -> str:
    return raw.strip()


def _evaluate_precise(points: List[_Point], relevant_text: str) -> None:
    """Resolve number / date / location points against the relevant image text."""
    img = _extract_facts(relevant_text)
    low = relevant_text.lower()

    for p in points:
        if p.kind == "number":
            value, kind = p.data
            same_kind = [(v, k, r) for v, k, r in img.numbers if k == kind or (k == "count" and kind == "money")]
            if any(abs(v - value) < 1e-9 * max(1.0, abs(value)) for v, _k, _r in same_kind):
                p.status = "matched"
            elif any(k == kind for _v, k, _r in img.numbers):
                shown = ", ".join(_fmt_num(r) for v, k, r in img.numbers if k == kind)
                p.status, p.detail = "contradicted", f"claim says {p.display}, image text says {shown}"
            # else: missing
        elif p.kind == "date":
            cd = p.data
            conflicts, matched, others = [], False, False
            for d, m, y, raw in img.dates:
                idt = (d, m, y)
                if any(c is not None and i is not None and c != i for c, i in zip(cd, idt)):
                    conflicts.append(raw)
                elif all(c is None or i is not None for c, i in zip(cd, idt)):
                    matched = True
                else:
                    others = True
            if matched:
                p.status = "matched"
            elif conflicts and not others:
                p.status, p.detail = "contradicted", f"claim says {p.display}, image text says {', '.join(conflicts)}"
        elif p.kind == "location":
            cl = p.data
            if re.search(rf"\b{re.escape(p.display.lower())}\b", low) or any(_loc_eq(cl, c) for c, _ in img.locations):
                p.status = "matched"
            else:
                rivals = [raw for c, raw in img.locations if c in GAZETTEER or raw.lower() in GAZETTEER]
                if cl in GAZETTEER and rivals:
                    p.status, p.detail = "contradicted", f"claim says {p.display}, image text says {', '.join(rivals)}"


# ----------------------------------------------------------------------------
# OCR quality
# ----------------------------------------------------------------------------
def ocr_quality_score(ocr: OcrResult) -> float:
    """0.0-1.0 trust in the OCR, derived from the existing Phase 4 OCR result."""
    if not ocr.available or ocr.status != "SUCCESS" or not ocr.text:
        return 0.0
    if ocr.confidence is None:
        return {"high": 0.85, "moderate": 0.65, "low": 0.30}.get(ocr.ocr_quality, 0.50)
    return round(max(0.0, min(1.0, ocr.confidence / 100.0)), 2)


# ----------------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------------
def _snippet(text: str, n: int = 140) -> str:
    return text if len(text) <= n else text[: n - 1].rstrip() + "…"


def _result(rel: str, quality: float, explanation: str, extracted: str = "", relevant: str = "",
            matched: Optional[List[str]] = None, contradicted: Optional[List[str]] = None,
            missing: Optional[List[str]] = None) -> ImageTextEvidence:
    return ImageTextEvidence(
        extracted_text=extracted[:MAX_EXTRACTED_CHARS],
        relevant_text=relevant[:MAX_EXTRACTED_CHARS],
        relationship=rel,  # type: ignore[arg-type]
        matched_claim_points=matched or [],
        contradicted_claim_points=contradicted or [],
        missing_claim_points=missing or [],
        explanation=explanation,
        ocr_quality=quality,
        source="uploaded_image",
    )


def compare_image_text_to_claim(ocr: OcrResult, claim_text: str) -> ImageTextEvidence:
    """Compare the (existing Phase 4) OCR text of an image with the user's claim."""
    quality = ocr_quality_score(ocr)
    claim = (claim_text or "").strip()

    if not claim:
        return _result("INSUFFICIENT_TEXT", quality, "No user claim was provided to compare the image text against.")
    if not ocr.available:
        return _result("INSUFFICIENT_TEXT", quality, "OCR was unavailable, so the image text could not be read or compared.")
    if ocr.status == "NO_TEXT_DETECTED" or not ocr.text.strip():
        return _result("INSUFFICIENT_TEXT", quality, "No readable text was detected in the image.")

    text, kept_ratio = clean_ocr_text(ocr.text)
    meaningful = [w for w in _words(text) if len(w) >= 2 and w not in STOPWORDS]

    if quality < MIN_OCR_QUALITY or kept_ratio < MIN_CLEAN_RATIO:
        return _result(
            "INSUFFICIENT_TEXT", quality,
            f"OCR quality is too low ({int(quality * 100)}%) to compare the image text with the claim reliably.",
            extracted=text,
        )
    if len(meaningful) < MIN_MEANINGFUL_TOKENS:
        return _result(
            "INSUFFICIENT_TEXT", quality,
            "The image contains too little readable text to compare with the claim.",
            extracted=text,
        )

    points = _claim_points(claim)
    topical = [p for p in points if p.kind in ("entity", "term")]
    if not topical:
        return _result(
            "INSUFFICIENT_TEXT", quality,
            "The claim has too few checkable facts (no identifiable entities or events) to compare with the image text.",
            extracted=text,
        )

    # 1. Topical relevance against the full image text
    for p in topical:
        p.status = "matched" if _topical_match(p, text) else "missing"
    matched_topical = [p for p in topical if p.status == "matched"]
    share = len(matched_topical) / len(topical)
    if not matched_topical or (share < 0.34 and len(matched_topical) < 2):
        return _result(
            "UNRELATED", quality,
            f"The text found in the image (\"{_snippet(text, 100)}\") does not appear to relate to the claim.",
            extracted=text,
            missing=[f"{p.kind}: {p.display}" for p in points],
        )

    # 2. Relevant passage = sentences that carry matched topical points, plus neighbours
    sents = _sentences(text) or [text]
    hit = {i for i, s in enumerate(sents) if any(_topical_match(p, s) for p in matched_topical)}
    idx = sorted({j for i in hit for j in (i - 1, i, i + 1) if 0 <= j < len(sents)}) if len(sents) > 1 else [0]
    relevant = " ".join(sents[i] for i in idx)

    # 3. Precise facts (numbers, dates, locations) inside the relevant passage
    precise = [p for p in points if p.kind in ("number", "date", "location")]
    _evaluate_precise(precise, relevant)

    # 4. Denial / debunk cues ("FAKE", "denied", ...) in the relevant passage
    denial = DENIAL_RE.search(relevant)
    claim_has_denial = bool(DENIAL_RE.search(claim))
    denial_note = ""
    if denial and not claim_has_denial:
        denial_note = f"image text flags the claim as '{denial.group(0).lower()}'"

    matched = [f"{p.kind}: {p.display}" for p in points if p.status == "matched"]
    contradicted = [f"{p.kind}: {p.detail}" for p in points if p.status == "contradicted"]
    if denial_note:
        contradicted.append(f"denial: {denial_note}")
    missing = [f"{p.kind}: {p.display}" for p in points if p.status == "missing"]
    quote = _snippet(relevant)
    caveat = " This reflects what the image states, not whether it is true."

    if contradicted:
        rel = "CONTRADICTS"
        expl = (f"The image contains text stating \"{quote}\", which contradicts the claim: "
                f"{'; '.join(contradicted)}.{caveat}")
    elif not missing:
        rel = "SUPPORTS"
        expl = (f"The image contains text stating \"{quote}\", which supports the claim; all "
                f"{len(matched)} checked point(s) match.{caveat}")
    else:
        rel = "PARTIALLY_SUPPORTS"
        expl = (f"The image contains text stating \"{quote}\", which supports part of the claim "
                f"({', '.join(matched[:4])}) but does not mention: {', '.join(missing[:4])}.{caveat}")

    return _result(rel, quality, expl, extracted=text, relevant=relevant,
                   matched=matched, contradicted=contradicted, missing=missing)
