# core/receipt_ai.py

import base64
import json
from io import BytesIO
from PIL import Image
import fitz  # PyMuPDF
from openai import OpenAI


def get_openai_client(api_key: str):
    return OpenAI(api_key=api_key)


def image_to_base64(image: Image.Image) -> str:
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def pdf_to_images(uploaded_file, max_pages=3):
    pdf_bytes = uploaded_file.read()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    images = []
    for page_num in range(min(len(doc), max_pages)):
        page = doc[page_num]
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        img = Image.open(BytesIO(pix.tobytes("png")))
        images.append(img)

    return images


def extract_receipt_data(client, image: Image.Image, model="gpt-4.1-mini") -> dict:
    image_b64 = image_to_base64(image)

    prompt = """
Extract structured bookkeeping data from this receipt, bill, invoice, or payment document.

Return ONLY valid JSON.

Fields:
{
  "transaction_type": "expense or income",
  "date": "YYYY-MM-DD or empty",
  "vendor_or_customer": "merchant/vendor/customer name",
  "description": "short description",
  "category": "Meals, Tools, Software, Office Expense, Employee Cost, Contractor Payment, Rent, Utilities, Internet/Phone, Vehicle, Marketing, Professional Fees, Insurance, Bank Fees, Travel, Income, Uncategorized",
  "subtotal": number,
  "tax": number,
  "total": number,
  "currency": "CAD or unknown",
  "confidence": "high, medium, low",
  "notes": "short note"
}

Rules:
- If this is a purchase receipt or bill, transaction_type = expense.
- If this is an invoice issued to a customer or client payment, transaction_type = income.
- If unsure, use expense.
- Use total as the final amount paid or received.
- If tax is not visible, use 0.
- If category is unclear, use Uncategorized.
"""

    response = client.chat.completions.create(
        model=model,
        temperature=0,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_b64}"
                        }
                    }
                ]
            }
        ]
    )

    content = response.choices[0].message.content

    try:
        return json.loads(content)
    except Exception:
        return {
            "transaction_type": "expense",
            "date": "",
            "vendor_or_customer": "",
            "description": content,
            "category": "Uncategorized",
            "subtotal": 0,
            "tax": 0,
            "total": 0,
            "currency": "unknown",
            "confidence": "low",
            "notes": "AI response could not be parsed as JSON"
        }
