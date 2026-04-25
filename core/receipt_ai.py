# core/receipt_ai.py

import base64
import json
from io import BytesIO

import fitz  # PyMuPDF
from PIL import Image
from openai import OpenAI


def get_client(api_key: str):
    return OpenAI(api_key=api_key)


def image_to_base64(image: Image.Image) -> str:
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def pdf_to_images(uploaded_file, max_pages: int = 3):
    pdf_bytes = uploaded_file.read()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    images = []

    for i in range(min(len(doc), max_pages)):
        page = doc[i]
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        image = Image.open(BytesIO(pix.tobytes("png"))).convert("RGB")
        images.append(image)

    return images


def extract_bill_details(client, image: Image.Image, model: str = "gpt-4.1-mini") -> dict:
    image_b64 = image_to_base64(image)

    prompt = """
Analyze this bill, receipt, invoice, or payment document.

Extract the details needed for an Excel bookkeeping table.

Important:
- The image may be rotated, tilted, folded, or slightly unclear.
- Read the receipt carefully.
- Return the final amount paid as total.
- For Quebec receipts, GST/TPS and QST/TVQ should be included in tax.
- If this is a store receipt, it is usually an expense.
- If this is an invoice issued to a client/customer, it is income.
- If subtotal is not clearly visible, use 0.
- If tax is not clearly visible, use 0.
- If total is not clearly visible, use 0.
"""

    schema = {
        "name": "bill_extraction",
        "schema": {
            "type": "object",
            "properties": {
                "transaction_type": {
                    "type": "string",
                    "enum": ["expense", "income"]
                },
                "date": {
                    "type": "string"
                },
                "name": {
                    "type": "string"
                },
                "description": {
                    "type": "string"
                },
                "category": {
                    "type": "string",
                    "enum": [
                        "Meals",
                        "Tools",
                        "Software",
                        "Office Expense",
                        "Employee Cost",
                        "Contractor Payment",
                        "Rent",
                        "Utilities",
                        "Internet/Phone",
                        "Vehicle",
                        "Marketing",
                        "Professional Fees",
                        "Insurance",
                        "Bank Fees",
                        "Travel",
                        "Income",
                        "Uncategorized"
                    ]
                },
                "subtotal": {
                    "type": "number"
                },
                "tax": {
                    "type": "number"
                },
                "total": {
                    "type": "number"
                },
                "currency": {
                    "type": "string"
                },
                "confidence": {
                    "type": "string",
                    "enum": ["high", "medium", "low"]
                }
            },
            "required": [
                "transaction_type",
                "date",
                "name",
                "description",
                "category",
                "subtotal",
                "tax",
                "total",
                "currency",
                "confidence"
            ],
            "additionalProperties": False
        },
        "strict": True
    }

    response = client.chat.completions.create(
        model=model,
        temperature=0,
        response_format={
            "type": "json_schema",
            "json_schema": schema
        },
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a precise receipt, bill, and invoice extraction engine. "
                    "Return only structured JSON that matches the schema."
                )
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_b64}",
                            "detail": "high"
                        }
                    }
                ]
            }
        ]
    )

    content = response.choices[0].message.content
    extracted = json.loads(content)

    return {
        "transaction_type": extracted.get("transaction_type", "expense"),
        "date": extracted.get("date", ""),
        "name": extracted.get("name", ""),
        "description": extracted.get("description", ""),
        "category": extracted.get("category", "Uncategorized"),
        "subtotal": float(extracted.get("subtotal", 0) or 0),
        "tax": float(extracted.get("tax", 0) or 0),
        "total": float(extracted.get("total", 0) or 0),
        "currency": extracted.get("currency", "CAD"),
        "confidence": extracted.get("confidence", "medium")
    }
