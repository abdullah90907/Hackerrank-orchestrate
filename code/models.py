from dataclasses import dataclass
from pathlib import Path


@dataclass
class SupportDocument:
    doc_id: str
    company_key: str
    company_name: str
    title: str
    source_url: str
    breadcrumbs: str
    text: str
    file_path: Path