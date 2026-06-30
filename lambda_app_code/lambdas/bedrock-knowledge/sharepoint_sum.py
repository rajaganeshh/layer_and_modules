import fitz
import base64
import json
import os
import time
import boto3
import asyncio
from botocore.exceptions import ClientError


IMAGE_SAVE_DIR = "/tmp/pdf_images"
os.makedirs(IMAGE_SAVE_DIR, exist_ok=True)

# =====================================================
# HELPER: Bedrock LLM invoke (sync)
# =====================================================

def _invoke_bedrock_llm(region_name, prompt, llm_model, max_tokens=800, temperature=0):
    """Invoke Bedrock model synchronously."""
    client = boto3.client("bedrock-runtime", region_name=region_name)

    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": [
            {"role": "user", "content": [{"type": "text", "text": prompt}]}
        ],
    }

    response = client.invoke_model(modelId=llm_model, body=json.dumps(body))
    model_response = json.loads(response["body"].read())

    return model_response["content"][0]["text"].strip()


# =====================================================
# STEP 1: Extract PDF text & images
# =====================================================

def extract_pdf_content(pdf_path):
    """Extract all text and images from the PDF."""
    doc = fitz.open(pdf_path)
    all_text = ""
    image_paths = []
 
    # Ensure folder exists
    os.makedirs(IMAGE_SAVE_DIR, exist_ok=True)
 
    for page_num, page in enumerate(doc, start=1):
        all_text += page.get_text("text") + "\n"
 
        for img_index, img in enumerate(page.get_images(full=True), start=1):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
 
            image_filename = f"page{page_num}_img{img_index}.png"
            image_path = os.path.join(IMAGE_SAVE_DIR, image_filename)
 
            print(f"[DEBUG] Saving image to: {image_path}")
            # make sure folder exists again (safe guard)
            os.makedirs(os.path.dirname(image_path), exist_ok=True)
 
            with open(image_path, "wb") as f:
                f.write(image_bytes)
 
            image_paths.append(image_path)
 
    return all_text.strip(), image_paths

# =====================================================
# STEP 2: Describe images using Bedrock 
# =====================================================

def _describe_image_sync(image_path, region_name, llm_model):
    """Describe a single image synchronously using Bedrock multimodal model."""
    with open(image_path, "rb") as img_file:
        b64_img = base64.b64encode(img_file.read()).decode("utf-8")

    prompt = f"Describe this image (file: {os.path.basename(image_path)})."

    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 300,
        "temperature": 0,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": b64_img}}
                ]
            }
        ]
    }

    client = boto3.client("bedrock-runtime", region_name=region_name)
    response = client.invoke_model(modelId=llm_model, body=json.dumps(body))
    model_response = json.loads(response["body"].read())

    return f"{os.path.basename(image_path)}: {model_response['content'][0]['text'].strip()}"


async def describe_images_async(image_paths, region_name, llm_model):
    """Run image descriptions concurrently."""
    tasks = []
    for img_path in image_paths:
        tasks.append(asyncio.to_thread(_describe_image_sync, img_path, region_name, llm_model))
    return await asyncio.gather(*tasks, return_exceptions=True)


# =====================================================
# STEP 3: Text chunking
# =====================================================

def chunk_text(text, max_chars=9000):
    """Split text into manageable chunks."""
    chunks = []
    while len(text) > max_chars:
        split_at = text[:max_chars].rfind(".")
        if split_at == -1:
            split_at = max_chars
        chunks.append(text[:split_at + 1].strip())
        text = text[split_at + 1:]
    if text.strip():
        chunks.append(text.strip())
    return chunks


# =====================================================
# STEP 4: Summarize chunks (async)
# =====================================================

def _summarize_text_chunk_sync(chunk, idx, region_name, llm_model):
    """Summarize one text chunk synchronously."""
    prompt = f"""
Summarize part {idx} of the document:

{chunk}

Strictly follow these rules:

1. Summary Content Requirements:
The summary must include the following components with the given numbered structure only(Don't add ** for these bullet points)
   1. Context: Describe what the article talks about.
   2. Components: Describe the main components or key parts.
   3. Integrations: Explain how the components work together.
   4. Points of Failure: Describe potential weaknesses or failure points.

2. Strict Rules:
   - Do not hallucinate or add information not in the original text.
   - No commentary beyond the summary.
   - Keep tone factual and consistent.
"""
    return _invoke_bedrock_llm(region_name, prompt, llm_model, max_tokens=600)


async def summarize_chunks_async(chunks, region_name, llm_model):
    """Summarize text chunks concurrently."""
    tasks = []
    for idx, chunk in enumerate(chunks, start=1):
        tasks.append(asyncio.to_thread(_summarize_text_chunk_sync, chunk, idx, region_name, llm_model))
    return await asyncio.gather(*tasks, return_exceptions=True)


# =====================================================
# STEP 5: Combine all into a final summary
# =====================================================

def _combine_summaries_sync(text_chunks, image_descriptions, region_name, llm_model):
    combined_input = f"""
Below are the partial summaries of the document:

{text_chunks}

And here are the image descriptions extracted from the PDF:

{image_descriptions}

Combine all these into a single unified summary using the same four-numbered structure:
The summary must include the following components with the given numbered structure only(Don't add ** for these bullet points)
1. Context: Describe what the article talks about.
2. Components: Describe the main components or key parts.
3. Integrations: Explain how the components work together.
4. Points of Failure: Describe potential weaknesses or failure points.

Follow these summary length rules:
- If original text ≥ 300 words → make the summary exactly 300 words.
- If < 300 words → make summary 100 words.
- If < 100 words → match original length.
- If < 50 words → return the text as is.
"""
    return _invoke_bedrock_llm(region_name, combined_input, llm_model, max_tokens=800)


# =====================================================
# MAIN ASYNC WORKFLOW
# =====================================================

async def summarize_pdf_with_bedrock_async(pdf_path, region_name, llm_model):
    start_total = time.time()
    print("Extracting PDF content...")

    text, image_paths = extract_pdf_content(pdf_path)
    print(f"Found {len(image_paths)} images.")
    print(f"Image saved at : {image_paths}") #

    text_chunks = chunk_text(text)
    print(f"Split into {len(text_chunks)} text chunks.")
    print("Starting concurrent summarization and image analysis...")

    chunk_summaries, image_descriptions = await asyncio.gather(
        summarize_chunks_async(text_chunks, region_name, llm_model),
        describe_images_async(image_paths, region_name, llm_model)
    )

    # Handle exceptions
    chunk_summaries = [s if isinstance(s, str) else f"[Error: {s}]" for s in chunk_summaries]
    image_descriptions = [d if isinstance(d, str) else f"[Error: {d}]" for d in image_descriptions]

    print("Combining all summaries...")
    final_summary = await asyncio.to_thread(_combine_summaries_sync, chunk_summaries, image_descriptions, region_name, llm_model)


    end_total = time.time()
    print(f"\n Done! Total time: {end_total - start_total:.2f}s")
    return final_summary

