import csv
from typing import Dict, List


def load_documents_from_csv(file_path: str) -> List[Dict[str, str]]:
    documents: List[Dict[str, str]] = []
    with open(file_path, newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            documents.append(
                {
                    "title": row["title"],
                    "snippet": row["snippet"],
                    "category": row["category"],
                    "source": row.get("source", "csv-ingest"),
                }
            )
    return documents

