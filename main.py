import json
import os
import argparse
import datetime
from pathlib import Path
from tqdm import tqdm

from src.core.data_loader import DataLoader
from src.core.prompt_builder import build_prompt_text
from src.models.gpt import GPTModel
from src.models.claude import ClaudeModel
from src.models.gemini import GeminiModel

def main():
    parser = argparse.ArgumentParser(description="Run Extraction Task")
    parser.add_argument("--model", type=str, required=True, choices=["gpt", "claude", "gemini"], help="Model family to use")
    parser.add_argument("--mode", type=str, required=True, choices=["zero-shot", "few-shot"], help="Prompting mode")
    parser.add_argument("--pmcids", type=str, nargs="*", help="List of specific PMCIDs to run")
    parser.add_argument("--model_version", type=str, help="Specific model version string (optional)")

    args = parser.parse_args()

    # 1. Setup
    loader = DataLoader()

    # 2. Select Model
    model_version = args.model_version
    if args.model == "gpt":
        if not model_version: model_version = "gpt-4o" # "GPT-5.1"
        model_engine = GPTModel(model_name=model_version)
    elif args.model == "claude":
        if not model_version: model_version = "claude-3-opus-20240229" # "Claude Opus 4.5"
        model_engine = ClaudeModel(model_name=model_version)
    elif args.model == "gemini":
        if not model_version: model_version = "gemini-1.5-pro-latest" # "Gemini 3 Pro"
        model_engine = GeminiModel(model_name=model_version)

    # 3. Determine PMCIDs
    if args.pmcids:
        target_pmcids = args.pmcids
    else:
        target_pmcids = loader.list_target_pmcids()

    print(f"Targeting {len(target_pmcids)} documents using {args.model} ({model_version}) in {args.mode} mode.")

    # 4. Prepare Output Directory
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(f"outputs/{args.model}/{args.mode}/{timestamp}")
    output_dir.mkdir(parents=True, exist_ok=True)

    # 5. Load Few-Shot Examples (if needed)
    few_shot_data = []
    if args.mode == "few-shot":
        few_shot_data = loader.get_few_shot_examples()
        print(f"Loaded {len(few_shot_data)} few-shot examples.")

    # 6. Run Loop
    results = []

    for pmcid in tqdm(target_pmcids):
        # a. Get PDF Path
        pdf_path = loader.get_pdf_path(pmcid)
        if not pdf_path:
            print(f"Skipping PMCID {pmcid}: PDF not found.")
            continue

        # b. Get ICOs
        icos = loader.get_icos(pmcid)
        if not icos:
            print(f"Skipping PMCID {pmcid}: No ICOs found in gold standard.")
            continue

        # c. Build Prompt Text
        prompt_text = build_prompt_text(icos, mode=args.mode)

        # d. Generate
        try:
            raw_output = model_engine.generate(
                pdf_path=pdf_path,
                prompt_text=prompt_text,
                few_shot_examples=few_shot_data
            )

            # e. Basic Cleaning/Parsing (JSON extraction)
            # The model might return ```json ... ``` or just text.
            clean_output = raw_output.strip()
            if clean_output.startswith("```json"):
                clean_output = clean_output.replace("```json", "", 1)
            if clean_output.startswith("```"):
                clean_output = clean_output.replace("```", "", 1)
            if clean_output.endswith("```"):
                clean_output = clean_output.rsplit("```", 1)[0]
            clean_output = clean_output.strip()

            # Try to parse to ensure validity
            try:
                parsed_json = json.loads(clean_output)
            except json.JSONDecodeError:
                # Store raw if parse fails
                parsed_json = {"error": "JSONDecodeError", "raw": clean_output}

            # Save per-file output? Or aggregate?
            # User requested: "When outputed the whole run: it should have format: model, few/zero-shot,timepoint. It should output clean json where each ICO is a row."

            # We will accumulate specific rows.
            # Assuming parsed_json is a list of dicts (one per ICO)
            if isinstance(parsed_json, list):
                for item in parsed_json:
                    item['pmcid'] = pmcid
                    results.append(item)
            elif isinstance(parsed_json, dict):
                 parsed_json['pmcid'] = pmcid
                 results.append(parsed_json)

        except Exception as e:
            print(f"Error processing {pmcid}: {e}")
            results.append({"pmcid": pmcid, "error": str(e)})

    # 7. Write Final Output
    output_file = output_dir / "extracted_data.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"Run complete. Results saved to {output_file}")

if __name__ == "__main__":
    main()
