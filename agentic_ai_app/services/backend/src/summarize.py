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
A. Summary Content Requirements
   The summary must include the following on generating the summary (Don't add ** for these bullet points):
   1. Describe what the article talks about and its objective.
   2. Summarize the main components of the application described in the article by providing its name and its functionality.
   3. Summarize how the applications are integrated by providing their names, CI, and integration details.
   4. Describe potential weaknesses, failure points, or symptoms that are described in the article or can be inferred from components or integrations.

B. Strict Rules
   - If the contents to be summarized are process-related and not technical (such as about an application or integrations), then don't summarize. Provide output as "NIL".
   - If there is no content related to components or their integrations or points of failure of an application, do not provide any details for those sections.
   - Do not hallucinate or add any information not found in the original text.
   - Do not include any text or commentary beyond the summary.
   - Keep the tone factual and consistent with the source.
   - Don't add any heading in the summary output. Let it be a free flow summary.

Summary Length Rules
   - Maximum summary length can be 300 words.
   - Minimum summary length can be 20 words or less.

Text to summarize:
{text}
"""
    return _invoke_bedrock_llm(region_name, prompt, llm_model)