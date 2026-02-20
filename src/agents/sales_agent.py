"""Shufi -- AI sales agent for SmartShopper.

Model: Claude Sonnet 4.6
Language: Hebrew only
Scope: Shopping and price comparison only

Conversation flow:
- Generic product ("טלפון") -> asks brand -> budget -> priority -> search
- Specific product ("אייפון 15 פרו") -> asks location -> search
- Smart: detects budget/brand info even if given in wrong step
"""

from __future__ import annotations

import logging
import re
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum, auto

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from src.config import get_settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
אתה "שופי", סוכן מכירות חכם של SmartShopper.

כללים מחייבים:
1. דבר רק בעברית.
2. אישיות: חם, ידידותי, מכירתי. אתה אוהב לעזור ללקוחות.
3. מקסימום 3 שורות בכל תשובה.
4. תמיד סיים בשאלה אחת בדיוק.
5. נושאים מותרים בלבד: מוצרים, מחירים, משלוחים, חנויות, קניות, השוואת מחירים.
6. כל נושא אחר (פוליטיקה, דת, רגשות, חדשות, בדיחות, תכנות): \
ענה בדיוק "אני יכול לעזור רק בנושא קניות 😊 מה תרצה לחפש היום?"
7. אל תמציא מחירים. אם שואלים כמה עולה משהו — אמור שתבדוק.
8. "יקר לי" / "לא בתקציב" — הצע חלופות זולות, שאל מה התקציב, היה אופטימי.

אתה עוזר ללקוחות למצוא מוצרים מ-15+ חנויות ישראליות כולל משלוח עם שיליחויות בע"מ."""

# --- Detection helpers ---

BRANDS = {
    "אייפון", "iphone", "סמסונג", "samsung", "galaxy", "גלקסי",
    "שיאומי", "xiaomi", "redmi", "poco", "וואווי", "huawei",
    "sony", "סוני", "jbl", "bose", "apple", "אפל",
    "lg", "אל ג'י", "lenovo", "לנובו", "dell", "דל",
    "asus", "אסוס", "hp", "acer", "איסר",
    "dyson", "דייסון", "philips", "פיליפס", "bosch", "בוש",
    "nikon", "ניקון", "canon", "קנון", "gopro",
    "nintendo", "נינטנדו", "playstation", "ps5", "xbox",
    "airpods", "אירפודס", "macbook", "מקבוק", "ipad", "אייפד",
}

GENERIC_CATEGORIES = {
    "טלפון", "פלאפון", "נייד", "סלולרי",
    "אוזניות", "אוזניה", "רמקול", "רמקולים",
    "טלוויזיה", "טלויזיה", "מסך", "מחשב", "לפטופ",
    "מקרר", "מכונת כביסה", "מדיח", "מייבש", "תנור", "מיקרוגל",
    "שואב אבק", "מזגן", "מאוורר",
    "מצלמה", "שעון חכם", "טאבלט",
    "קונסולה", "משחק", "אופניים", "קורקינט",
}

ISRAELI_CITIES = {
    "תל אביב", "ירושלים", "חיפה", "באר שבע", "אשדוד", "אשקלון",
    "נתניה", "חולון", "בת ים", "רמת גן", "פתח תקווה", "ראשון לציון",
    "הרצליה", "רעננה", "כפר סבא", "הוד השרון", "רחובות", "נס ציונה",
    "לוד", "רמלה", "מודיעין", "עפולה", "נצרת", "טבריה", "אילת",
    "קריית שמונה", "קריית גת", "דימונה", "ערד", "צפת",
    "מרכז", "צפון", "דרום", "שרון", "גוש דן", "שפלה", "נגב",
}

_GREETINGS = {"היי", "הי", "שלום", "בוקר טוב", "ערב טוב", "מה נשמע", "מה קורה", "אהלן"}
_OFF_TOPIC = {"פוליטיקה", "ממשלה", "דת", "אלוהים", "בחירות", "מלחמה", "כדורגל"}
_PRICE_WORDS = {"יקר", "זול", "מחיר", "עולה", "עולות", "עולים", "תקציב", "כסף"}

MAX_HISTORY = 10


def _is_specific_product(text: str) -> bool:
    lower = text.lower()
    has_brand = any(b in lower for b in BRANDS)
    has_number = bool(re.search(r"\d", text))
    has_model_word = any(w in lower for w in ("פרו", "pro", "max", "ultra", "plus", "lite", "mini"))
    return has_brand and (has_number or has_model_word)


def _is_generic_product(text: str) -> bool:
    lower = text.lower().strip()
    return any(cat in lower for cat in GENERIC_CATEGORIES)


def _extract_budget(text: str) -> str | None:
    """Extract a budget number from text like 'עד 1500', 'משהו עד 2000', '1500'."""
    m = re.search(r"(\d[\d,]*)", text)
    return m.group(1).replace(",", "") if m else None


def _has_brand(text: str) -> str | None:
    """Extract brand name from text."""
    lower = text.lower()
    for brand in BRANDS:
        if brand in lower:
            return brand
    return None


def _has_location(text: str) -> str | None:
    """Extract city/area from text."""
    lower = text.lower().strip()
    for city in ISRAELI_CITIES:
        if city in lower:
            return city
    return None


def _fallback_chat(text: str) -> str:
    lower = text.lower().strip()
    if any(g in lower for g in _GREETINGS):
        return "היי! אני שופי, העוזר האישי שלך לקניות.\nאני סורק 15+ חנויות ומוצא לך את העסקאות הכי טובות. מה נחפש?"
    if any(w in lower for w in _OFF_TOPIC):
        return "אני מתמחה רק בקניות והשוואת מחירים.\nמה תרצה לחפש?"
    if any(w in lower for w in _PRICE_WORDS):
        return "אני אמצא לך בדיוק מה שאתה צריך במחיר שמתאים לך!\nאיזה מוצר מעניין אותך?"
    return "אני כאן כדי לעזור לך למצוא את המוצר המושלם.\nספר לי מה אתה מחפש?"


# --- Conversation state machine ---

class ConvState(Enum):
    IDLE = auto()
    ASKING_BRAND = auto()
    ASKING_BUDGET = auto()
    ASKING_PRIORITY = auto()
    ASKING_LOCATION = auto()


@dataclass
class UserSession:
    state: ConvState = ConvState.IDLE
    product_query: str = ""
    brand: str = ""
    budget: str = ""
    priority: str = ""
    location: str = ""
    is_specific: bool = False
    messages: list[BaseMessage] = field(default_factory=list)


class SalesAgent:
    """Shufi -- conversational sales agent with smart intent detection."""

    def __init__(self) -> None:
        settings = get_settings()
        api_key = settings.llm.anthropic_api_key

        self._llm: ChatAnthropic | None = None
        if api_key and not api_key.startswith("sk-ant-your-"):
            self._llm = ChatAnthropic(
                model="claude-sonnet-4-6",
                api_key=api_key,
                max_tokens=256,
                temperature=0.7,
            )

        self._sessions: dict[int, UserSession] = defaultdict(UserSession)

    @property
    def available(self) -> bool:
        return self._llm is not None

    async def handle_message(self, user_id: int, text: str) -> tuple[str, bool]:
        """Process message through state machine. Returns (response, should_search)."""
        session = self._sessions[user_id]

        # --- IDLE: detect what the user wants ---
        if session.state == ConvState.IDLE:
            if _is_specific_product(text):
                session.product_query = text
                session.is_specific = True
                # Check if location is already in the text
                loc = _has_location(text)
                if loc:
                    session.location = loc
                    self._reset_session(user_id)
                    return f"מצוין! מחפש {text}...", True
                session.state = ConvState.ASKING_LOCATION
                resp = await self._llm_respond(user_id, text)
                return resp or f"בחירה מעולה! באיזה אזור אתה נמצא כדי שאחשב משלוח?", False

            if _is_generic_product(text):
                session.product_query = text
                session.is_specific = False
                # Maybe user already included budget: "טלפון עד 2000"
                budget = _extract_budget(text)
                brand = _has_brand(text)
                if budget:
                    session.budget = budget
                if brand:
                    session.brand = brand
                session.state = ConvState.ASKING_BRAND
                resp = await self._llm_respond(user_id, text)
                return resp or f"יופי, {text}! יש לי גישה ל-15+ חנויות.\nאיזה מותג או דגם מעניין אותך? או שתרצה שאני אמליץ?", False

            # Not a product -- general chat
            resp = await self._llm_respond(user_id, text)
            return resp or _fallback_chat(text), False

        # --- Smart collection: parse what the user gave, fill what's missing ---
        self._smart_extract(session, text)

        # Check if we have enough info to search
        if session.is_specific:
            # Specific product: just need location
            if session.location:
                query = session.product_query
                location = session.location
                self._reset_session(user_id)
                return f"מעולה! מחפש {query} באזור {location}...", True
            session.state = ConvState.ASKING_LOCATION
            resp = await self._llm_respond(user_id, text)
            return resp or "באיזה אזור אתה נמצא?", False

        # Generic product: need brand + budget + priority
        missing = self._what_is_missing(session)
        if not missing:
            query = self._build_query(session)
            self._reset_session(user_id)
            return f"מצוין, יש לי את כל מה שצריך! מחפש {query}...", True

        # Ask for the next missing piece
        session.state = missing
        resp = await self._llm_respond(user_id, text)
        if resp:
            return resp, False
        return self._fallback_question(session, missing), False

    def _smart_extract(self, session: UserSession, text: str) -> None:
        """Extract brand, budget, location, priority from any user message."""
        budget = _extract_budget(text)
        if budget and not session.budget:
            session.budget = budget

        brand = _has_brand(text)
        if brand and not session.brand:
            session.brand = brand

        location = _has_location(text)
        if location and not session.location:
            session.location = location

        # If nothing specific was extracted, use as answer for current state
        if not budget and not brand and not location:
            if session.state == ConvState.ASKING_BRAND and not session.brand:
                session.brand = text
            elif session.state == ConvState.ASKING_BUDGET and not session.budget:
                session.budget = text
            elif session.state == ConvState.ASKING_PRIORITY and not session.priority:
                session.priority = text
            elif session.state == ConvState.ASKING_LOCATION and not session.location:
                session.location = text

    def _what_is_missing(self, session: UserSession) -> ConvState | None:
        """Return the next state to ask about, or None if all collected."""
        if not session.brand:
            return ConvState.ASKING_BRAND
        if not session.budget:
            return ConvState.ASKING_BUDGET
        if not session.priority:
            return ConvState.ASKING_PRIORITY
        return None

    def _fallback_question(self, session: UserSession, missing: ConvState) -> str:
        """Natural Hebrew question for missing info."""
        product = session.product_query
        if missing == ConvState.ASKING_BRAND:
            return f"יופי! יש המון אפשרויות ב{product}.\nאיזה מותג מעניין אותך? אם לא בטוח, אני יכול להמליץ."
        if missing == ConvState.ASKING_BUDGET:
            brand_info = f" של {session.brand}" if session.brand else ""
            return f"מה התקציב שלך ל{product}{brand_info}? ככה אוכל למצוא בדיוק מה שמתאים."
        if missing == ConvState.ASKING_PRIORITY:
            return "מה הכי חשוב לך? איכות, מחיר נמוך, או מותג מסוים?"
        if missing == ConvState.ASKING_LOCATION:
            return "באיזה אזור אתה נמצא? זה עוזר לי לחשב משלוח מדויק."
        return "ספר לי עוד על מה שאתה מחפש."

    def _build_query(self, session: UserSession) -> str:
        parts = [session.product_query]
        if session.brand:
            parts.append(session.brand)
        if session.budget:
            parts.append(f"עד {session.budget}")
        return " ".join(parts)

    async def _llm_respond(self, user_id: int, text: str) -> str:
        """Get LLM response. Returns empty string if unavailable."""
        if not self._llm:
            return ""

        session = self._sessions[user_id]
        session.messages.append(HumanMessage(content=text))

        if len(session.messages) > MAX_HISTORY:
            session.messages[:] = session.messages[-MAX_HISTORY:]

        context = SYSTEM_PROMPT
        if session.product_query:
            info_parts = [f"מוצר: {session.product_query}"]
            if session.brand:
                info_parts.append(f"מותג: {session.brand}")
            if session.budget:
                info_parts.append(f"תקציב: {session.budget}")
            if session.priority:
                info_parts.append(f"עדיפות: {session.priority}")
            if session.location:
                info_parts.append(f"מיקום: {session.location}")
            context += "\n\nמידע שנאסף: " + ", ".join(info_parts)

            missing = self._what_is_missing(session) if not session.is_specific else None
            if session.is_specific and not session.location:
                context += "\nשאל באיזה אזור הלקוח נמצא."
            elif missing == ConvState.ASKING_BRAND:
                context += "\nשאל איזה מותג/דגם מעניין אותו."
            elif missing == ConvState.ASKING_BUDGET:
                context += "\nשאל מה התקציב שלו."
            elif missing == ConvState.ASKING_PRIORITY:
                context += "\nשאל מה הכי חשוב לו (איכות/מחיר/מותג)."

        messages: list[BaseMessage] = [SystemMessage(content=context), *session.messages]

        try:
            response = await self._llm.ainvoke(messages)
            content = response.content if isinstance(response.content, str) else str(response.content)
            session.messages.append(AIMessage(content=content))
            return content
        except Exception:
            logger.exception("Shufi LLM call failed")
            return ""

    def _reset_session(self, user_id: int) -> None:
        self._sessions[user_id] = UserSession()

    def clear_history(self, user_id: int) -> None:
        self._sessions.pop(user_id, None)


# Singleton
shufi = SalesAgent()
