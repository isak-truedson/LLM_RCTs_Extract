import json
import argparse
from pathlib import Path
import unicodedata
import re

def normalize_value(v):
    if v is None:
        return None
    s = str(v).strip().lower()
    if s in {"", "none", "nr", "not reported", "n/a", "na", "not extractable"}:
        return None
    if s.endswith("%"):
        s = s[:-1].strip()
    try:
        return float(s)
    except ValueError:
        return None

def normalize_name(s):
    if s is None: return None
    s = unicodedata.normalize("NFKC", str(s))
    s = s.lower()
    s = " ".join(s.split())
    return s

def evaluate_run(run_file_path, gold_standard_path):
    # Load Run Data
    with open(run_file_path, "r", encoding="utf-8") as f:
        run_data = json.load(f)

    # Load Gold Standard
    with open(gold_standard_path, "r", encoding="utf-8") as f:
        gold_data = json.load(f)

    # Index Gold Data by (pmcid, intervention, comparator, outcome)
    gold_map = {}
    for entry in gold_data:
        pmcid = str(entry.get('pmcid'))
        i = normalize_name(entry.get('intervention'))
        c = normalize_name(entry.get('comparator'))
        o = normalize_name(entry.get('outcome'))
        key = (pmcid, i, c, o)
        gold_map[key] = entry

    # Metrics
    metrics = {
        "tp": 0, "fp": 0, "fn": 0,
        "fields": {
            "group_size": {"tp": 0, "fp": 0, "fn": 0},
            "events": {"tp": 0, "fp": 0, "fn": 0},
            "mean": {"tp": 0, "fp": 0, "fn": 0},
            "sd": {"tp": 0, "fp": 0, "fn": 0},
        }
    }

    # Evaluate
    # We iterate over Gold Standard to find what was matched (Recall)
    # And iterate over Prediction to find extras (Precision context, though complex with exact matching)

    # Simplified approach: Iterate Gold, look for match in Run.
    # But Run data might not have the normalized key.

    # Index Run Data
    run_map = {}
    for entry in run_data:
        pmcid = str(entry.get('pmcid'))
        i = normalize_name(entry.get('intervention'))
        c = normalize_name(entry.get('comparator'))
        o = normalize_name(entry.get('outcome'))
        key = (pmcid, i, c, o)
        # Handle duplicates? Last one wins?
        run_map[key] = entry

    # Compare Fields
    # Fields to check:
    # Binary: intervention_events, comparator_events, intervention_group_size, comparator_group_size
    # Continuous: intervention_mean, comparator_mean, intervention_sd, comparator_sd, groups...

    fields_map = {
        "intervention_events": "events",
        "comparator_events": "events",
        "intervention_group_size": "group_size",
        "comparator_group_size": "group_size",
        "intervention_mean": "mean",
        "comparator_mean": "mean",
        "intervention_standard_deviation": "sd",
        "comparator_standard_deviation": "sd"
    }

    for key, gold_entry in gold_map.items():
        pred_entry = run_map.get(key)

        # Determine if this gold entry is relevant (Binary vs Continuous)
        # Check what fields are present in gold
        for gold_field, metric_type in fields_map.items():
            g_val = normalize_value(gold_entry.get(gold_field))

            if g_val is not None:
                # We have a gold fact
                if pred_entry:
                    p_val = normalize_value(pred_entry.get(gold_field))
                    if p_val == g_val:
                        metrics["fields"][metric_type]["tp"] += 1
                        metrics["tp"] += 1
                    else:
                        metrics["fields"][metric_type]["fp"] += 1 # Wrong value
                        metrics["fp"] += 1
                else:
                    metrics["fields"][metric_type]["fn"] += 1 # Missing prediction
                    metrics["fn"] += 1

    # Calculate Summaries
    print("Evaluation Results:")
    print(f"Total Gold Facts: {metrics['tp'] + metrics['fp'] + metrics['fn']}")
    print(f"Total TP: {metrics['tp']}")
    print(f"Total FP (Mismatch): {metrics['fp']}")
    print(f"Total FN (Missing): {metrics['fn']}")

    precision = metrics['tp'] / (metrics['tp'] + metrics['fp']) if (metrics['tp'] + metrics['fp']) > 0 else 0
    recall = metrics['tp'] / (metrics['tp'] + metrics['fn']) if (metrics['tp'] + metrics['fn']) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    print(f"Micro Precision: {precision:.3f}")
    print(f"Micro Recall: {recall:.3f}")
    print(f"Micro F1: {f1:.3f}")

    return metrics

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("run_file", help="Path to the output JSON file")
    parser.add_argument("--gold", default="data/gold_standard/annotated_rct_dataset.json", help="Path to gold standard")
    args = parser.parse_args()

    evaluate_run(args.run_file, args.gold)
