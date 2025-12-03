def build_prompt_text(icos, mode="zero-shot"):
    """
    Constructs the text portion of the prompt.

    Args:
        icos: List of dictionaries containing Intervention, Comparator, Outcome.
        mode: "zero-shot" or "few-shot".

    Returns:
        str: The prompt text.
    """

    # Base instructions
    instructions = (
        "You are an expert meta-analyst. Your task is to extract statistical results "
        "from the provided clinical trial PDF report.\n\n"
        "For each specific Intervention-Comparator-Outcome (ICO) triplet listed below, "
        "extract the arm-level statistics found in the paper.\n\n"
        "REQUIRED OUTPUT FORMAT:\n"
        "Provide the output as a clean JSON list. Each item in the list should correspond "
        "to one of the requested ICOs. Do not include markdown formatting (like ```json) "
        "or any preamble/postscript text. Just the raw JSON.\n\n"
        "The JSON schema for each item is:\n"
        "{\n"
        "  \"intervention\": \"<Intervention Name>\",\n"
        "  \"comparator\": \"<Comparator Name>\",\n"
        "  \"outcome\": \"<Outcome Name>\",\n"
        "  \"intervention_group_size\": <number or null>,\n"
        "  \"comparator_group_size\": <number or null>,\n"
        "  \"intervention_events\": <number or null>,\n"
        "  \"comparator_events\": <number or null>,\n"
        "  \"intervention_mean\": <number or null>,\n"
        "  \"comparator_mean\": <number or null>,\n"
        "  \"intervention_standard_deviation\": <number or null>,\n"
        "  \"comparator_standard_deviation\": <number or null>,\n"
        "  \"notes\": \"<Any relevant notes or 'Not reported'>\"\n"
        "}\n\n"
        "If a value is not reported, use null.\n"
        "For binary outcomes, focus on events/group size.\n"
        "For continuous outcomes, focus on mean/sd/group size.\n"
    )

    # Specific ICOs to extract
    ico_section = "EXTRACT DATA FOR THE FOLLOWING ICOs:\n"
    for i, ico in enumerate(icos, 1):
        ico_section += (
            f"{i}. Intervention: {ico['intervention']}\n"
            f"   Comparator: {ico['comparator']}\n"
            f"   Outcome: {ico['outcome']} ({ico.get('outcome_type', 'unknown')})\n"
        )

    # Combine
    full_prompt = f"{instructions}\n\n{ico_section}\n\n"

    if mode == "few-shot":
        # Note: The actual PDF content for few-shot examples will be handled
        # by the model wrapper (attaching files or interleaving content).
        # This text serves as the final instruction for the target PDF.
        full_prompt += "Please extract the data for the document provided above (or attached)."
    else:
        full_prompt += "Please extract the data for the document provided."

    return full_prompt
