import json
import boto3
import os
from botocore.exceptions import ClientError

# ====================== INVOKING LLM ============================

def _invoke_bedrock_llm(region_name, prompt, llm_model):
    """Call LLM with a given prompt"""

    
    client = boto3.client("bedrock-runtime", region_name=region_name)

    native_request = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 300,
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


def summarize_text(text: str, region_name: str, llm_model) -> str:
    """Summarize input text in about 50 words """
    prompt = f"Summarize the following text in about 50 words:\n\n{text}"
    return _invoke_bedrock_llm(region_name, prompt, llm_model)
