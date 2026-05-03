import sys
from pathlib import Path

import pandas as pd

from agent import process_ticket
from config import DATA_DIR, SAMPLE_TICKETS_PATH, FINAL_TICKETS_PATH, OUTPUT_PATH
from corpus_loader import load_corpus
from retriever import CorpusRetriever


OUTPUT_COLUMNS = [
    "status",
    "product_area",
    "response",
    "justification",
    "request_type",
]


def get_value(row, possible_names):
    for name in possible_names:
        if name in row:
            value = row[name]
            if pd.isna(value):
                return ""
            return str(value)
    return ""


def normalize_label(value):
    return str(value or "").strip().lower()


def build_retriever():
    print("Loading corpus")
    documents = load_corpus(DATA_DIR)
    print(f"Loaded documents: {len(documents)}")

    print("Building retriever")
    retriever = CorpusRetriever(documents)
    print("Retriever ready")

    return retriever


def run_sample_mode(retriever):
    print("Reading sample tickets")
    sample_df = pd.read_csv(SAMPLE_TICKETS_PATH)
    print(f"Sample rows: {len(sample_df)}")

    correct_status = 0
    correct_request_type = 0

    for index, row in sample_df.iterrows():
        issue = get_value(row, ["issue", "Issue"])
        subject = get_value(row, ["subject", "Subject"])
        company = get_value(row, ["company", "Company"])

        predicted = process_ticket(
            retriever=retriever,
            issue=issue,
            subject=subject,
            company=company,
        )

        expected_status = normalize_label(get_value(row, ["status", "Status"]))
        expected_request_type = normalize_label(get_value(row, ["request_type", "Request Type"]))

        predicted_status = normalize_label(predicted["status"])
        predicted_request_type = normalize_label(predicted["request_type"])

        if predicted_status == expected_status:
            correct_status += 1

        if predicted_request_type == expected_request_type:
            correct_request_type += 1

        print("")
        print("=" * 80)
        print(f"Sample row: {index + 1}")
        print(f"Issue: {issue}")
        print(f"Company: {company}")
        print("")
        print(f"Expected status: {expected_status}")
        print(f"Predicted status: {predicted_status}")
        print("")
        print(f"Expected request type: {expected_request_type}")
        print(f"Predicted request type: {predicted_request_type}")
        print("")
        print(f"Predicted product area: {predicted['product_area']}")
        print(f"Response: {predicted['response']}")
        print(f"Justification: {predicted['justification']}")

    print("")
    print("=" * 80)
    print("Sample check summary")
    print(f"Status correct: {correct_status} of {len(sample_df)}")
    print(f"Request type correct: {correct_request_type} of {len(sample_df)}")


def run_final_mode(retriever):
    print("Reading final support tickets")
    tickets_df = pd.read_csv(FINAL_TICKETS_PATH)
    print(f"Final rows: {len(tickets_df)}")

    output_rows = []

    status_counts = {}
    request_type_counts = {}

    for index, row in tickets_df.iterrows():
        issue = get_value(row, ["issue", "Issue"])
        subject = get_value(row, ["subject", "Subject"])
        company = get_value(row, ["company", "Company"])

        predicted = process_ticket(
            retriever=retriever,
            issue=issue,
            subject=subject,
            company=company,
        )

        clean_row = {
            "status": predicted["status"],
            "product_area": predicted["product_area"],
            "response": predicted["response"],
            "justification": predicted["justification"],
            "request_type": predicted["request_type"],
        }

        output_rows.append(clean_row)

        status_counts[clean_row["status"]] = status_counts.get(clean_row["status"], 0) + 1
        request_type_counts[clean_row["request_type"]] = request_type_counts.get(clean_row["request_type"], 0) + 1

        print("")
        print("=" * 80)
        print(f"Final row: {index + 1}")
        print(f"Issue: {issue}")
        print(f"Company: {company}")
        print(f"Status: {clean_row['status']}")
        print(f"Request type: {clean_row['request_type']}")
        print(f"Product area: {clean_row['product_area']}")
        print(f"Response: {clean_row['response']}")
        print(f"Justification: {clean_row['justification']}")

    output_df = pd.DataFrame(output_rows, columns=OUTPUT_COLUMNS)

    output_path = Path(OUTPUT_PATH)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_df.to_csv(output_path, index=False)

    print("")
    print("=" * 80)
    print("Final output written")
    print(str(output_path))
    print("")
    print("Status counts")
    for key, value in status_counts.items():
        print(f"{key}: {value}")

    print("")
    print("Request type counts")
    for key, value in request_type_counts.items():
        print(f"{key}: {value}")


def main():
    mode = "sample"

    if len(sys.argv) >= 2:
        mode = sys.argv[1].strip().lower()

    if mode not in {"sample", "final"}:
        print("Usage:")
        print("python code/main.py sample")
        print("python code/main.py final")
        raise SystemExit(1)

    retriever = build_retriever()

    if mode == "sample":
        run_sample_mode(retriever)
    else:
        run_final_mode(retriever)


if __name__ == "__main__":
    main()