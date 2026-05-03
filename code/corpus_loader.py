import os
from pathlib import Path
from typing import Dict, List, Tuple

from config import SUPPORTED_COMPANIES
from models import SupportDocument


def read_text_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except FileNotFoundError:
        if os.name == "nt":
            long_path = "\\\\?\\" + str(path.resolve())
            with open(long_path, "r", encoding="utf-8", errors="ignore") as file:
                return file.read()
        raise


def split_front_matter(raw_text: str) -> Tuple[Dict[str, str], str]:
    front_marker = chr(45) * 3

    text = raw_text.strip()

    if not text.startswith(front_marker):
        return {}, raw_text

    parts = text.split(front_marker, 2)

    if len(parts) < 3:
        return {}, raw_text

    metadata_text = parts[1].strip()
    body_text = parts[2].strip()

    metadata = {}

    current_key = None
    list_items = []

    for line in metadata_text.splitlines():
        clean_line = line.strip()

        if not clean_line:
            continue

        if clean_line.startswith("#"):
            continue

        if clean_line.startswith(chr(45)):
            if current_key:
                item_value = clean_line.lstrip(chr(45)).strip().strip('"').strip("'")
                list_items.append(item_value)
            continue

        if ":" in clean_line:
            if current_key and list_items:
                metadata[current_key] = " > ".join(list_items)
                list_items = []

            key, value = clean_line.split(":", 1)
            current_key = key.strip()
            metadata[current_key] = value.strip().strip('"').strip("'")

    if current_key and list_items:
        metadata[current_key] = " > ".join(list_items)

    return metadata, body_text


def extract_heading(body_text: str) -> str:
    for line in body_text.splitlines():
        clean_line = line.strip()
        if clean_line.startswith("#"):
            return clean_line.lstrip("#").strip()
    return ""


def normalize_title_from_path(path: Path) -> str:
    name = path.stem.replace("_", " ")
    return " ".join(word.capitalize() for word in name.split())


def clean_body_text(text: str) -> str:
    lines = []

    for line in text.splitlines():
        clean_line = line.strip()

        if not clean_line:
            continue

        lower_line = clean_line.lower()

        if clean_line.startswith("#"):
            continue

        if lower_line.startswith("_last updated") or lower_line.startswith("_last modified"):
            continue

        if clean_line.startswith("!["):
            continue

        if clean_line.startswith("<img"):
            continue

        if clean_line.startswith("\\"):
            continue

        lines.append(clean_line)

    return "\n".join(lines)


def load_corpus(data_dir: Path) -> List[SupportDocument]:
    documents = []

    if not data_dir.exists():
        raise FileNotFoundError(f"Data folder not found: {data_dir}")

    for company_key, company_name in SUPPORTED_COMPANIES.items():
        company_dir = data_dir / company_key

        if not company_dir.exists():
            continue

        md_files = sorted(company_dir.rglob("*.md"))

        for file_path in md_files:
            raw_text = read_text_file(file_path)
            metadata, body_text = split_front_matter(raw_text)

            title = metadata.get("title", "").strip()
            if not title:
                title = extract_heading(body_text)
            if not title:
                title = normalize_title_from_path(file_path)

            source_url = metadata.get("source_url", "").strip()
            breadcrumbs = metadata.get("breadcrumbs", "").strip()
            clean_text = clean_body_text(body_text)

            doc_id = f"{company_key}:{file_path.relative_to(company_dir).as_posix()}"

            document = SupportDocument(
                doc_id=doc_id,
                company_key=company_key,
                company_name=company_name,
                title=title,
                source_url=source_url,
                breadcrumbs=breadcrumbs,
                text=clean_text,
                file_path=file_path,
            )

            documents.append(document)

    return documents