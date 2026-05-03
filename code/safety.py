from typing import List, Tuple

from classifier import contains_any, normalize_text
from retriever import RetrievedDocument


def get_top_score(retrieved: List[RetrievedDocument]) -> float:
    if not retrieved:
        return 0.0
    return retrieved[0].score


def get_score_gap(retrieved: List[RetrievedDocument]) -> float:
    if len(retrieved) < 2:
        return get_top_score(retrieved)
    return retrieved[0].score - retrieved[1].score


def get_top_document_text(retrieved: List[RetrievedDocument]) -> str:
    if not retrieved:
        return ""

    document = retrieved[0].document

    return normalize_text(
        f"{document.company_name} {document.title} {document.breadcrumbs} {document.text[:1600]}"
    )


def top_document_has_body(retrieved: List[RetrievedDocument]) -> bool:
    if not retrieved:
        return False

    text = retrieved[0].document.text.strip()
    return len(text) >= 120


def is_broad_platform_issue(text: str) -> bool:
    patterns = [
        "site is down",
        "platform is down",
        "service is down",
        "none of the pages",
        "all pages",
        "everything is down",
        "nothing is loading",
        "cannot access anything",
        "none of the submissions",
        "across any challenges",
        "stopped working completely",
        "all requests are failing",
    ]

    return contains_any(text, patterns)


def is_out_of_scope_request(text: str) -> bool:
    unrelated_patterns = [
        "iron man",
        "actor",
        "movie",
        "weather",
        "joke",
        "recipe",
        "poem",
    ]

    return contains_any(text, unrelated_patterns)


def is_public_guidance_request(text: str) -> bool:
    guidance_patterns = [
        "how do i",
        "how can i",
        "where can i",
        "what do i do",
        "what should i do",
        "can you provide",
        "please provide",
        "steps",
        "step by step",
        "report",
        "contact",
        "find",
        "learn more",
        "how long",
        "why",
    ]

    return contains_any(text, guidance_patterns)


def is_direct_account_action_request(text: str) -> bool:
    action_patterns = [
        "refund asap",
        "give me the refund",
        "give me refund",
        "please refund",
        "need a refund",
        "want a refund",
        "request a refund",
        "do it for me",
        "change my score",
        "increase my score",
        "move me forward",
        "approve my refund",
        "refund me today",
        "refund me now",
        "reverse this charge",
        "ban the seller",
        "restore my access",
        "give me access",
        "unlock my account",
        "remove the admin",
        "make me owner",
        "update it",
        "update my certificate",
        "name is incorrect",
        "remove them from our",
        "remove an interviewer",
        "employee has left",
        "filling in the forms",
        "fill in the forms",
        "reschedule",
        "rescheduling",
        "alternative date",
        "extend inactivity times",
    ]

    return contains_any(text, action_patterns)


def is_high_risk_topic(text: str) -> bool:
    risk_patterns = [
        "refund",
        "payment issue",
        "paid product",
        "fraud",
        "identity theft",
        "unauthorized transaction",
        "hacked",
        "account hacked",
        "security vulnerability",
        "vulnerability",
        "exploit",
        "data breach",
        "chargeback",
        "billing error",
        "charged twice",
        "payment failed",
        "score dispute",
        "plagiarism",
        "cheating",
        "proctoring violation",
        "admin removed",
        "permission removed",
        "blocked",
        "carte visa",
        "règles internes",
        "internal rules",
        "exact logic",
    ]

    return contains_any(text, risk_patterns)


def document_supports_public_guidance(text: str, retrieved: List[RetrievedDocument]) -> bool:
    if not retrieved:
        return False

    top_document_text = get_top_document_text(retrieved)

    support_terms = [
        "report",
        "contact",
        "support",
        "steps",
        "select",
        "click",
        "call",
        "request",
        "delete",
        "manage",
        "configure",
        "set up",
        "view",
        "access",
        "download",
        "block",
        "crawler",
        "dispute",
        "cash",
        "assistance",
    ]

    return contains_any(top_document_text, support_terms)


def metadata_indicates_relevance(retrieved: List[RetrievedDocument]) -> bool:
    if not retrieved:
        return False

    top = retrieved[0]

    if top.metadata_score >= 0.08:
        return True

    if top.overlap_score >= 0.12:
        return True

    title = normalize_text(top.document.title)
    breadcrumbs = normalize_text(top.document.breadcrumbs)

    useful_support_terms = [
        "test",
        "assessment",
        "candidate",
        "account",
        "conversation",
        "privacy",
        "card",
        "cheque",
        "billing",
        "subscription",
        "workspace",
        "event",
        "microsite",
        "report",
        "access",
        "delete",
        "duration",
        "expiration",
        "certificate",
        "crawler",
        "lti",
        "canvas",
        "dispute",
        "cash",
    ]

    return contains_any(f"{title} {breadcrumbs}", useful_support_terms)


def evidence_is_strong(retrieved: List[RetrievedDocument]) -> bool:
    if not retrieved:
        return False

    top_score = get_top_score(retrieved)
    score_gap = get_score_gap(retrieved)
    top = retrieved[0]

    if top_score >= 0.22:
        return True

    if top_score >= 0.16 and top.metadata_score >= 0.18:
        return True

    if top_score >= 0.13 and top.overlap_score >= 0.18 and score_gap >= 0.015:
        return True

    return False


def evidence_is_weak(retrieved: List[RetrievedDocument]) -> bool:
    if not retrieved:
        return True

    top_score = get_top_score(retrieved)
    top = retrieved[0]

    if top_score < 0.10:
        return True

    if top_score < 0.13 and top.metadata_score < 0.10:
        return True

    return False


def has_mismatched_business_context(text: str, retrieved: List[RetrievedDocument]) -> bool:
    if not retrieved:
        return True

    top_text = get_top_document_text(retrieved)

    business_admin_terms = [
        "infosec",
        "security process",
        "filling in the forms",
        "fill in the forms",
        "remove employee",
        "employee has left",
        "remove them",
        "remove an interviewer",
        "inactivity times",
        "hr lobby",
        "certificate name",
        "name is incorrect",
    ]

    if not contains_any(text, business_admin_terms):
        return False

    expected_terms = [
        "admin",
        "owner",
        "user",
        "team",
        "member",
        "interviewer",
        "certificate",
        "security",
        "compliance",
        "inactivity",
        "permission",
        "billing",
    ]

    return not contains_any(top_text, expected_terms)


def should_escalate(
    issue: str,
    subject: str,
    request_type: str,
    retrieved: List[RetrievedDocument],
) -> Tuple[bool, str]:
    text = normalize_text(f"{subject} {issue}")

    if request_type == "invalid" or is_out_of_scope_request(text):
        return False, "The ticket is outside the supported domains and can be answered with a brief out of scope response."

    if not retrieved:
        return True, "No relevant support document was found in the provided corpus."

    if is_broad_platform_issue(text):
        return True, "The ticket reports a broad platform availability issue that needs human review."

    if contains_any(text, ["refund", "payment", "paid", "charged"]) and contains_any(text, ["stopped", "failed", "not working", "error", "bug"]):
        return True, "The ticket combines a product failure with a payment or refund request, so it needs human support review."

    if is_direct_account_action_request(text):
        return True, "The ticket asks for an account or business specific action that should be handled by human support."

    if has_mismatched_business_context(text, retrieved):
        return True, "The retrieved article does not clearly match the requested account, admin, or business support action."

    if not top_document_has_body(retrieved):
        return True, "The retrieved support document does not contain enough body content to answer safely."

    strong_evidence = evidence_is_strong(retrieved)
    weak_evidence = evidence_is_weak(retrieved)
    public_guidance = is_public_guidance_request(text)
    risky_topic = is_high_risk_topic(text)
    corpus_has_guidance = document_supports_public_guidance(text, retrieved)

    if risky_topic:
        if public_guidance and strong_evidence and corpus_has_guidance:
            return False, "The ticket involves a sensitive topic, but the corpus provides public guidance that can be safely shared."
        return True, "The ticket is sensitive or account specific and should be reviewed by human support."

    if request_type == "bug":
        if strong_evidence and public_guidance:
            return False, "The corpus provides relevant troubleshooting guidance for this bug report."
        return True, "The ticket appears to be a bug and does not have enough clear corpus support for a direct answer."

    if weak_evidence:
        if public_guidance and metadata_indicates_relevance(retrieved) and corpus_has_guidance:
            return False, "The ticket asks for public support guidance and the retrieved article metadata indicates relevant corpus support."
        return True, "The retrieved support evidence is too weak to answer safely from the corpus."

    return False, "The issue is supported by relevant corpus evidence and does not require human escalation."