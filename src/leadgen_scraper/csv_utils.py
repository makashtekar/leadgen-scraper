import csv
from pathlib import Path
from typing import Any


def save_to_csv(data: list[dict[str, Any]], filename: str | Path) -> None:
    if not data:
        return

    filepath = Path(filename)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "business_name",
        "contact_phone",
        "whatsapp_number",
        "address",
        "products",
        "search_keyword",
        "source",
    ]

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(data)


def append_to_csv(data: list[dict[str, Any]], filename: str | Path) -> None:
    if not data:
        return

    filepath = Path(filename)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "business_name",
        "contact_phone",
        "whatsapp_number",
        "address",
        "products",
        "search_keyword",
        "source",
    ]

    write_header = not filepath.exists()
    with open(filepath, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        if write_header:
            writer.writeheader()
        writer.writerows(data)
