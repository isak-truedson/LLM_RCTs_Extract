import json
import os
import csv
from pathlib import Path

class DataLoader:
    def __init__(self, base_dir="."):
        self.base_dir = Path(base_dir)
        self.pdfs_dir = self.base_dir / "data" / "pdfs"
        self.gold_standard_json = self.base_dir / "data" / "gold_standard" / "annotated_rct_dataset.json"
        self.gold_standard_csv = self.base_dir / "data" / "gold_standard" / "annotated_rct_dataset.csv"
        self.examples_pdfs_dir = self.base_dir / "few_shots" / "examples_pdfs"
        self.examples_labels_dir = self.base_dir / "few_shots" / "examples_labels"

        # Cache for gold standard data
        self._gold_data = None

    def _load_gold_standard(self):
        if self._gold_data is None:
            # Prefer JSON if available and valid
            if self.gold_standard_json.exists():
                try:
                    with open(self.gold_standard_json, 'r', encoding='utf-8') as f:
                        self._gold_data = json.load(f)
                except json.JSONDecodeError:
                    print("Warning: JSON gold standard invalid, trying CSV.")

            # Fallback to CSV if JSON failed or missing
            if self._gold_data is None and self.gold_standard_csv.exists():
                self._gold_data = []
                with open(self.gold_standard_csv, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        self._gold_data.append(row)

            if self._gold_data is None:
                raise FileNotFoundError("Could not load gold standard data (checked JSON and CSV).")

        return self._gold_data

    def get_icos(self, pmcid):
        """
        Retrieve ICOs (Intervention, Comparator, Outcome) for a given PMCID.
        Returns a dictionary or list of ICOs.
        """
        gold_data = self._load_gold_standard()

        icos = []
        seen = set()

        for entry in gold_data:
            # Flexible PMCID matching (str/int)
            if str(entry.get('pmcid')) == str(pmcid):
                triplet = (
                    entry.get('intervention'),
                    entry.get('comparator'),
                    entry.get('outcome'),
                    entry.get('outcome_type')
                )
                if triplet not in seen:
                    seen.add(triplet)
                    icos.append({
                        "intervention": triplet[0],
                        "comparator": triplet[1],
                        "outcome": triplet[2],
                        "outcome_type": triplet[3],
                        "id": entry.get('id')
                    })
        return icos

    def get_pdf_path(self, pmcid):
        """
        Return the path to the PDF file for a given PMCID.
        Checks for {pmcid}.pdf or PMCID{pmcid}.pdf
        """
        # Try exact match
        path = self.pdfs_dir / f"{pmcid}.pdf"
        if path.exists():
            return path

        # Try with PMCID prefix if numeric
        path = self.pdfs_dir / f"PMCID{pmcid}.pdf"
        if path.exists():
            return path

        return None

    def list_target_pmcids(self):
        """
        List all PMCIDs found in the data/pdfs directory.
        """
        pmcids = []
        for f in self.pdfs_dir.glob("*.pdf"):
            # Extract numbers from filename
            name = f.stem
            # Simple heuristic: extract digits
            digits = "".join(filter(str.isdigit, name))
            if digits:
                pmcids.append(digits)
        return sorted(list(set(pmcids)))

    def get_few_shot_examples(self):
        """
        Returns a list of tuples: (pdf_path, label_json_content)
        """
        examples = []
        # Assuming matching filenames in examples_pdfs and examples_labels
        # e.g. 12345.pdf and 12345.json
        for pdf_file in self.examples_pdfs_dir.glob("*.pdf"):
            label_file = self.examples_labels_dir / f"{pdf_file.stem}.json"
            if label_file.exists():
                with open(label_file, 'r', encoding='utf-8') as f:
                    label_content = json.load(f)
                examples.append((pdf_file, label_content))
        return sorted(examples, key=lambda x: x[0].name)
