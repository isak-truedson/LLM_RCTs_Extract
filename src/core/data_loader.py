import json
import os
from pathlib import Path

class DataLoader:
    def __init__(self, base_dir="."):
        self.base_dir = Path(base_dir)
        self.pdfs_dir = self.base_dir / "data" / "pdfs"
        self.gold_standard_path = self.base_dir / "data" / "gold_standard" / "annotated_rct_dataset.json"
        self.examples_pdfs_dir = self.base_dir / "few_shots" / "examples_pdfs"
        self.examples_labels_dir = self.base_dir / "few_shots" / "examples_labels"

        # Cache for gold standard data
        self._gold_data = None

    def _load_gold_standard(self):
        if self._gold_data is None:
            with open(self.gold_standard_path, 'r', encoding='utf-8') as f:
                self._gold_data = json.load(f)
        return self._gold_data

    def get_icos(self, pmcid):
        """
        Retrieve ICOs (Intervention, Comparator, Outcome) for a given PMCID.
        Returns a dictionary or list of ICOs.
        """
        gold_data = self._load_gold_standard()

        # The gold standard is likely a list of extraction events.
        # We need to find unique ICO triplets for the given PMCID.
        # Assuming format from previous context: list of dicts with 'pmcid', 'intervention', 'comparator', 'outcome'

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
