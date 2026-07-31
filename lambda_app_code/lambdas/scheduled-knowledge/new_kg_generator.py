import os
import json
import boto3
from botocore.exceptions import ClientError

# ====================== CLEANING ============================

def clean_text(text: str) -> str:
    text = text.encode("utf-8").decode("unicode_escape", errors="ignore")
    try:
        text = text.encode("latin1").decode("utf-8")
    except Exception:
        pass

    replacements = {
        "’": "'",
        "‘": "'",
        "“": '"',
        "”": '"',
        "–": "-",
        "—": "-",
        "…": "...",
        "\n": " ",
    }
    for bad, good in replacements.items():
        text = text.replace(bad, good)

    return text.strip()


# ====================== CHUNKING ============================

def chunk_text(text, max_words=800):
    words = text.split()
    return [" ".join(words[i:i + max_words]) for i in range(0, len(words), max_words)]


# ====================== BEDROCK LLM ============================

def _invoke_bedrock_llm(region_name, llm_model, prompt):
    """Call LLM with the given prompt"""

    client = boto3.client("bedrock-runtime", region_name=region_name)

    native_request = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1024,
        "temperature": 0,
        "messages": [
            {
                "role": "user",
                "content": [{"type": "text", "text": prompt}],
            }
        ],
    }

    request = json.dumps(native_request)
    response = client.invoke_model(modelId=llm_model, body=request)
    model_response = json.loads(response["body"].read())

    return model_response["content"][0]["text"].strip()


# ====================== TRIPLET EXTRACTION ============================

def extract_triplet_json(chunk, region_name, llm_model):
    prompt = (
        "Extract a knowledge graph from the following text. "
        "Return only the JSON object with 'nodes' and 'edges' in the format below:\n\n"
        "{\n"
        "  \"nodes\": [\n"
        "    {\"id\": \"Node1\", \"description\": \"all lines from the text that mention Node1\"},\n"
        "    ...\n"
        "  ],\n"
        "  \"edges\": [\n"
        "    {\"source\": \"Node1\", \"target\": \"Node2\", \"label\": \"relationship\"},\n"
        "    ...\n"
        "  ]\n"
        "}\n\n"
        "Guidelines:\n"
        "- Copy descriptions exactly from the text (no summarization).\n"
        "- Preserve full sentences but do not add escape characters.\n"
        "- 'nodes' = unique entities, 'edges' = factual relationships.\n"
        "- Return valid JSON only.\n\n"
        f"Text:\n{chunk}"
    )

    raw_content = _invoke_bedrock_llm(region_name, llm_model, prompt)

    # Clean markdown wrappers if present
    if raw_content.startswith("```json") or raw_content.startswith("```"):
        raw_content = raw_content.strip("` \n")
        lines = raw_content.splitlines()
        if lines and lines[0].startswith("json"):
            lines = lines[1:]
        if lines and lines[-1] == "```":
            lines = lines[:-1]
        raw_content = "\n".join(lines)

    try:
        data = json.loads(raw_content)

        # Clean node descriptions
        if "nodes" in data:
            for node in data["nodes"]:
                if isinstance(node, dict) and "description" in node:
                    node["description"] = clean_text(node["description"])

        return data

    except Exception as e:
        return {"error": f"Invalid JSON: {str(e)}", "raw_response": raw_content}


# ====================== MAIN CREATOR ============================

def create_triplet_kg(input_text, region_name, llm_model):
    """Split text into chunks and extract knowledge graph triplets"""
    chunks = chunk_text(input_text)

    all_kg = {}
    for idx, chunk in enumerate(chunks):
        triplets = extract_triplet_json(chunk, region_name, llm_model)
        all_kg[f"chunk_{idx + 1}"] = triplets

    return all_kg
