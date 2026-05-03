import re
from typing import List, Set

from retriever import RetrievedDocument


def tokenize(text: str) -> Set[str]:
    words = re.findall(r"[A-Za-z0-9]+", text.lower())

    ignored = {
        "the",
        "and",
        "for",
        "with",
        "that",
        "this",
        "from",
        "have",
        "you",
        "your",
        "can",
        "how",
        "what",
        "where",
        "when",
        "why",
        "are",
        "was",
        "were",
        "will",
        "would",
        "could",
        "should",
        "please",
        "help",
        "need",
        "issue",
        "problem",
        "there",
        "here",
        "about",
        "into",
        "using",
        "also",
    }

    return {word for word in words if len(word) > 2 and word not in ignored}


def clean_markdown(text: str) -> str:
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = text.replace("**", "")
    text = text.replace("*", "")
    text = text.replace("_", "")
    text = text.replace("`", "")
    text = text.replace("#", "")

    cleaned_lines = []

    for line in text.splitlines():
        line = line.strip()

        if not line:
            continue

        if line.startswith("!"):
            continue

        if line.startswith("<img"):
            continue

        if line.startswith("\\"):
            continue

        cleaned_lines.append(line)

    return " ".join(cleaned_lines)


def split_into_passages(text: str) -> List[str]:
    passages = []
    current = []

    for line in text.splitlines():
        clean_line = line.strip()

        if not clean_line:
            if current:
                passages.append(" ".join(current))
                current = []
            continue

        current.append(clean_line)

        if len(" ".join(current)) > 500:
            passages.append(" ".join(current))
            current = []

    if current:
        passages.append(" ".join(current))

    return passages


def score_passage(query: str, passage: str) -> float:
    query_tokens = tokenize(query)
    passage_tokens = tokenize(passage)

    if not query_tokens or not passage_tokens:
        return 0.0

    overlap = query_tokens.intersection(passage_tokens)
    overlap_score = len(overlap) / max(len(query_tokens), 1)

    action_terms = {
        "click",
        "select",
        "log",
        "navigate",
        "contact",
        "call",
        "report",
        "delete",
        "request",
        "refund",
        "access",
        "manage",
        "view",
        "set",
        "modify",
        "extend",
        "invite",
        "reinvite",
        "cash",
        "urgent",
        "emergency",
        "assistance",
        "gcas",
        "cardholder",
        "cardholders",
        "lost",
        "stolen",
        "dispute",
        "charge",
        "issuer",
        "bank",
    }

    action_overlap = passage_tokens.intersection(action_terms)
    action_bonus = min(len(action_overlap) * 0.04, 0.16)

    priority_bonus = 0.0

    priority_terms = {
        "gcas",
        "emergency",
        "cash",
        "assistance",
        "cardholder",
        "cardholders",
        "global",
        "customer",
    }

    priority_overlap = passage_tokens.intersection(priority_terms)

    if priority_overlap:
        priority_bonus = min(len(priority_overlap) * 0.08, 0.32)

    return overlap_score + action_bonus + priority_bonus


def best_evidence_snippet(query: str, retrieved: List[RetrievedDocument], max_chars: int = 520) -> str:
    if not retrieved:
        return ""

    best_doc = retrieved[0].document
    passages = split_into_passages(best_doc.text)

    if not passages:
        return clean_markdown(best_doc.text[:max_chars])

    scored_passages = []

    for passage in passages:
        score = score_passage(query, passage)
        scored_passages.append((score, passage))

    query_tokens = tokenize(query)

    emergency_query_terms = {
        "urgent",
        "cash",
        "emergency",
        "gcas",
        "assistance",
        "cardholder",
        "cardholders",
    }

    if query_tokens.intersection(emergency_query_terms):
        boosted_passages = []

        for score, passage in scored_passages:
            passage_tokens = tokenize(passage)
            emergency_overlap = passage_tokens.intersection(emergency_query_terms)

            if emergency_overlap:
                score += min(len(emergency_overlap) * 0.20, 0.60)

            boosted_passages.append((score, passage))

        scored_passages = boosted_passages

    scored_passages.sort(key=lambda item: item[0], reverse=True)

    best_passage = scored_passages[0][1]
    snippet = clean_markdown(best_passage)

    if len(snippet) <= max_chars:
        return snippet

    shortened = snippet[:max_chars]
    if " " in shortened:
        shortened = shortened.rsplit(" ", 1)[0]

    return shortened + "."


def build_invalid_response() -> str:
    return (
        "I am sorry, but this request is outside the scope of this support agent. "
        "I can only help with support issues related to HackerRank, Claude, or Visa using the provided support documents."
    )


def build_escalation_response(product_area: str, reason: str) -> str:
    readable_area = product_area.replace("_", " ")

    return (
        f"This issue is related to {readable_area}. "
        f"It should be escalated to a human support specialist because {reason.lower()} "
        "I cannot safely resolve it from the provided support corpus alone."
    )


def build_grounded_response(
    retrieved: List[RetrievedDocument],
    product_area: str,
    issue: str = "",
    subject: str = "",
) -> str:
    readable_area = product_area.replace("_", " ")

    if not retrieved:
        return (
            f"This issue appears related to {readable_area}, but I could not find enough matching support documentation. "
            "Please contact support for further help."
        )

    best_doc = retrieved[0].document
    query = f"{subject} {issue}"
    if product_area == "emergency_services":
        query += " global customer assistance services gcas emergency cash urgent cash cardholder assistance"
    snippet = best_evidence_snippet(query, retrieved)

    response = (
        f"Based on the relevant support article, this issue falls under {readable_area}. "
        f"{snippet}"
    )

    if best_doc.source_url:
        response += f" Source: {best_doc.source_url}"

    return response


def build_justification(
    status: str,
    request_type: str,
    product_area: str,
    retrieved: List[RetrievedDocument],
    reason: str,
) -> str:
    readable_area = product_area.replace("_", " ")

    if retrieved:
        best_doc = retrieved[0].document
        return (
            f"Classified as {request_type} in {readable_area}. "
            f"Top document was '{best_doc.title}' with score {retrieved[0].score:.3f}. "
            f"Decision was {status} because {reason}"
        )

    return (
        f"Classified as {request_type} in {readable_area}. "
        f"Decision was {status} because {reason}"
    )