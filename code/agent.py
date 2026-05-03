from classifier import classify_request_type, infer_company_key, infer_product_area
from safety import should_escalate
from response_builder import (
    build_escalation_response,
    build_grounded_response,
    build_invalid_response,
    build_justification,
)


def process_ticket(retriever, issue, subject="", company=""):
    issue = str(issue or "")
    subject = str(subject or "")
    company = str(company or "")

    request_type = classify_request_type(issue, subject)
    company_key = infer_company_key(issue, subject, company)

    retrieved = retriever.search(
        query=f"{subject} {issue}",
        company_key=company_key,
        top_k=3,
    )

    product_area = infer_product_area(
        issue=issue,
        subject=subject,
        retrieved=retrieved,
        company_key=company_key,
    )

    escalate, reason = should_escalate(
        issue=issue,
        subject=subject,
        request_type=request_type,
        retrieved=retrieved,
    )

    if request_type == "invalid":
        status = "replied"
        response = build_invalid_response()
    elif escalate:
        status = "escalated"
        response = build_escalation_response(product_area, reason)
    else:
        status = "replied"
        response = build_grounded_response(
            retrieved=retrieved,
            product_area=product_area,
            issue=issue,
            subject=subject,
        )

    justification = build_justification(
        status=status,
        request_type=request_type,
        product_area=product_area,
        retrieved=retrieved,
        reason=reason,
    )

    return {
        "status": status,
        "product_area": product_area,
        "response": response,
        "justification": justification,
        "request_type": request_type,
    }