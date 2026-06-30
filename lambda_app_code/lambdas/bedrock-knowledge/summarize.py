import json
import boto3
import os
from botocore.exceptions import ClientError

# ====================== INVOKING LLM ============================

def _invoke_bedrock_llm(region_name, prompt, llm_model):

    client = boto3.client("bedrock-runtime", region_name=region_name)

    native_request = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 600,
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

    prompt = f"""
Summarize the following text strictly following these rules:

1. Summary Length Rules
   - If the original text has 300 words or more, make the summary exactly 300 words.
   - If the original text has less than 300 words, make the summary 100 words.
   - If the original text has less than 100 words, make the summary equal in word count to the original text.
   - If the original text has less than 50 words, give the text as it is . Example- Don't write extra text like "The text "dummy" contains only one word (5 words or less), which falls under the rule for texts with less than 50 words." for "dummy". just write the "dummy" for this case.  

2. Summary Content Requirements
   The summary must include the following components with the given numbered structure only(Don't add ** for these bullet points)
   1. Context: Describe what the article talks about.
   2. Components: Describe the main components or key parts.
   3. Integrations: Explain how the components work together.
   4. Points of Failure: Describe potential weaknesses or failure points.



3. Strict Rules
   - Do not hallucinate or add any information not found in the original text.
   - Do not include any text or commentary beyond the summary.
   - Keep the tone factual and consistent with the source.

Text to summarize:
{text}
"""

    return _invoke_bedrock_llm(region_name, prompt, llm_model)


