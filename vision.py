"""Vision step: send the uploaded photo to a Groq vision-capable model
and get back a plain-language description of what's visibly wrong.
"""
import base64
import os

from langchain.messages import HumanMessage
from langchain_groq import ChatGroq

VISION_MODEL = os.getenv("GROQ_VISION_MODEL", "qwen/qwen3.6-27b")

DESCRIBE_PROMPT = (
    "You are looking at a photo submitted as a facility, equipment, or product "
    "issue report. Describe in 2-4 concise sentences exactly what is visibly "
    "wrong (damage, defect, hazard, malfunction, wear, etc). Only describe what "
    "you can actually see in the image. Do not guess at the cause and do not "
    "recommend a fix — just describe the problem clearly enough that someone "
    "reading it later, without the photo, understands what was reported."
)


def describe_image(image_bytes: bytes, mime_type: str = "image/jpeg") -> str:
    """Return a short natural-language description of the issue shown in the photo."""
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    data_url = f"data:{mime_type};base64,{b64}"

    llm = ChatGroq(model=VISION_MODEL, temperature=0.2)
    message = HumanMessage(
        content=[
            {"type": "text", "text": DESCRIBE_PROMPT},
            {"type": "image_url", "image_url": {"url": data_url}},
        ]
    )
    response = llm.invoke([message])
    return response.content.strip()