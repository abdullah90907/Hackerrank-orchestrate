# Support Triage Agent

This folder contains a terminal based support triage agent for the HackerRank Orchestrate challenge.

## Approach

The agent uses a local corpus retrieval approach. It reads the provided Markdown support articles from the data folder, builds a TF IDF retrieval index, routes each ticket to the likely company domain, retrieves relevant support documents, applies safety and escalation checks, and writes the required CSV output.

The agent does not use live web search. It only uses the provided support corpus.

## Main components

config.py
Stores project paths and supported company names.

models.py
Defines the support document data structure.

corpus_loader.py
Loads Markdown support articles from the data folder. It extracts title, source URL, breadcrumbs, body text, company, and file path.

retriever.py
Builds a retrieval index over article body text and metadata. It combines body similarity, title and breadcrumb similarity, and token overlap.

classifier.py
Infers company, request type, and product area.

safety.py
Decides whether to reply or escalate. It escalates broad outages, weak evidence, account specific actions, payment or refund actions, security issues, and unsupported cases.

response_builder.py
Builds safe user facing responses from retrieved evidence. It selects the most relevant passage from the top support article.

agent.py
Runs the full ticket processing pipeline for one ticket.

main.py
Command line entry point for sample validation and final output generation.

## Install dependencies

Run from the repository root:

python -m pip install -r code/requirements.txt

## Run sample validation

Run from the repository root:

python code/main.py sample

This reads support_tickets/sample_support_tickets.csv and compares status and request_type against the expected sample labels.

## Generate final output

Run from the repository root:

python code/main.py final

This reads support_tickets/support_tickets.csv and writes predictions to:

support_tickets/output.csv

## Output columns

The generated CSV contains:

status
product_area
response
justification
request_type

Allowed status values:

replied
escalated

Allowed request type values:

product_issue
feature_request
bug
invalid

## Design notes

The sample tickets were used only for validation. The final logic is based on retrieval confidence, article metadata relevance, risk category, action type, and corpus support.

High risk or account specific tickets are escalated rather than guessed. Public guidance questions are answered only when the corpus provides relevant support evidence.