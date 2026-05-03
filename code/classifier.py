import re
from typing import List

from retriever import RetrievedDocument


VALID_REQUEST_TYPES = {
    "product_issue",
    "feature_request",
    "bug",
    "invalid",
}


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def contains_any(text: str, keywords: List[str]) -> bool:
    clean_text = normalize_text(text)
    return any(keyword in clean_text for keyword in keywords)


def classify_request_type(issue: str, subject: str = "") -> str:
    text = f"{subject} {issue}"
    clean_text = normalize_text(text)

    thank_only_patterns = [
        "thank you",
        "thank you for helping me",
        "thanks",
        "thanks for helping me",
        "thankyou",
    ]

    if clean_text in thank_only_patterns:
        return "invalid"

    unrelated_keywords = [
        "iron man",
        "actor",
        "movie",
        "weather",
        "joke",
        "poem",
        "recipe",
    ]

    unsafe_instruction_keywords = [
        "delete all files",
        "ignore previous",
        "show internal",
        "system prompt",
        "hidden rules",
        "internal rules",
        "logic exact",
        "exact logic",
    ]

    support_intent_keywords = [
        "hackerrank",
        "claude",
        "visa",
        "assessment",
        "candidate",
        "test",
        "score",
        "account",
        "login",
        "password",
        "conversation",
        "workspace",
        "billing",
        "payment",
        "refund",
        "card",
        "cheque",
        "transaction",
        "dispute",
        "fraud",
        "error",
        "bug",
        "not working",
        "cannot",
        "can't",
        "how do i",
        "where can i",
        "what do i do",
        "please can you",
    ]

    if contains_any(text, unrelated_keywords):
        return "invalid"

    if contains_any(text, unsafe_instruction_keywords) and not contains_any(text, support_intent_keywords):
        return "invalid"

    bug_keywords = [
        "bug",
        "error",
        "broken",
        "not working",
        "does not work",
        "failed",
        "failing",
        "crash",
        "crashed",
        "down",
        "not loading",
        "cannot access",
        "can't access",
        "stuck",
        "blank page",
        "all pages",
        "none of the pages",
        "none of the submissions",
        "across any challenges",
        "stopped working completely",
        "all requests are failing",
        "compatibility check",
        "compatible check",
    ]

    feature_keywords = [
        "feature request",
        "please add",
        "can you add",
        "add support for",
        "new feature",
        "wish there was",
        "it would be useful if",
    ]

    if contains_any(text, bug_keywords):
        return "bug"

    if contains_any(text, feature_keywords):
        return "feature_request"

    return "product_issue"


def infer_company_key(issue: str, subject: str, given_company: str) -> str:
    clean_company = normalize_text(given_company or "")

    if clean_company == "claude":
        return "claude"

    if clean_company == "hackerrank":
        return "hackerrank"

    if clean_company == "visa":
        return "visa"

    text = normalize_text(f"{subject} {issue}")

    claude_words = [
        "claude",
        "anthropic",
        "max plan",
        "team plan",
        "enterprise plan",
        "claude code",
        "conversation",
        "workspace",
        "bedrock",
        "lti",
    ]

    hackerrank_words = [
        "hackerrank",
        "assessment",
        "test invite",
        "candidate",
        "coding test",
        "challenge",
        "score",
        "proctor",
        "engage",
        "microsite",
        "interviewer",
        "certificate",
        "resume builder",
    ]

    visa_words = [
        "visa",
        "card",
        "cheque",
        "traveller",
        "traveler",
        "merchant",
        "transaction",
        "issuer",
        "bank",
        "dispute",
        "fraud",
        "cash",
    ]

    if contains_any(text, claude_words):
        return "claude"

    if contains_any(text, hackerrank_words):
        return "hackerrank"

    if contains_any(text, visa_words):
        return "visa"

    return ""


def clean_product_area(value: str) -> str:
    value = normalize_text(value)
    value = value.replace("&", "and")
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = value.strip("_")
    return value or "general_support"


def infer_product_area(
    issue: str,
    subject: str,
    retrieved: List[RetrievedDocument],
    company_key: str,
) -> str:
    text = normalize_text(f"{subject} {issue}")

    if "site is down" in text or "all pages" in text or "none of the pages" in text:
        return "platform_availability"

    if "none of the submissions" in text or "across any challenges" in text:
        return "platform_availability"

    if "stopped working completely" in text or "all requests are failing" in text:
        return "platform_availability"

    if not company_key:
        return "general_support"

    if "infosec" in text or "security process" in text or "filling in the forms" in text or "fill in the forms" in text:
        return "security_compliance"

    if "reschedule" in text or "rescheduling" in text or "alternative date" in text:
        return "assessments"

    if "inactivity" in text or "interviewer" in text or "hr lobby" in text or "screen share" in text:
        return "interviews"

    if "certificate" in text:
        return "certifications"

    if "employee has left" in text or "remove them" in text or "remove an interviewer" in text or "hiring account" in text:
        return "user_management"

    if "merchant" in text or "minimum" in text:
        return "merchant_support"

    if "urgent cash" in text or "emergency cash" in text:
        return "emergency_services"

    if "identity theft" in text or "fraud" in text or "unauthorized" in text:
        return "fraud_security"

    if "traveller" in text or "traveler" in text or "cheque" in text:
        return "travel_support"

    if "privacy" in text or "private info" in text or "temporary chat" in text:
        return "privacy"

    if "data" in text and ("improve" in text or "model" in text or "models" in text):
        return "privacy"

    if "crawler" in text or "crawling" in text or "robots" in text:
        return "privacy_and_legal"

    if "billing" in text or "refund" in text or "charged" in text or "payment" in text or "subscription" in text:
        return "billing"

    if "score" in text or "assessment" in text or "test" in text or "candidate" in text:
        return "assessments"

    if "microsite" in text or "event" in text or "engage" in text:
        return "engage"

    if "claude code" in text:
        return "claude_code"

    if "bedrock" in text:
        return "amazon_bedrock"

    if "lti" in text or "canvas" in text or "students" in text:
        return "claude_for_education"

    if retrieved:
        best_doc = retrieved[0].document

        if best_doc.breadcrumbs:
            first_area = best_doc.breadcrumbs.split(">")[0].strip()
            return clean_product_area(first_area)

        if best_doc.title:
            if company_key == "visa":
                return "general_support"

            words = best_doc.title.split()[:4]
            return clean_product_area(" ".join(words))

    return "general_support"