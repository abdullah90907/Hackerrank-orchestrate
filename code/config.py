from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = PROJECT_ROOT / "data"
TICKETS_DIR = PROJECT_ROOT / "support_tickets"

SAMPLE_TICKETS_PATH = TICKETS_DIR / "sample_support_tickets.csv"
FINAL_TICKETS_PATH = TICKETS_DIR / "support_tickets.csv"
OUTPUT_PATH = TICKETS_DIR / "output.csv"

SUPPORTED_COMPANIES = {
    "claude": "Claude",
    "hackerrank": "HackerRank",
    "visa": "Visa",
}