import base64
import json
from io import BytesIO

import fitz
from PIL import Image
from openai import OpenAI


def get_client(api_key: str):
    return OpenAI(api_key=api_key)


def image_to_base64(image: Image.Image) -> str:
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def pdf_to_images(uploaded_file, max_pages=3):
    pdf_bytes = uploaded_file.read()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    images = []
    for i in range(min(len(doc), max_pages)):
        page = doc[i]
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        image = Image.open(BytesIO(pix.tobytes("png"))).convert("RGB")
        images.append(image)

    return images


def extract_bill_details(client, image: Image.Image, model="gpt-4.1-mini") -> dict:
    image_b64 = image_to_base64(image)

    prompt = """
Analyze this bill, receipt, invoice, or payment document.

Extract only the details needed for an Excel bookkeeping table.

Return ONLY valid JSON in this format:

{
  "transaction_type": "expense or income",
  "date": "YYYY-MM-DD or empty",
  "name": "vendor name if expense, customer name if income",
  "description": "short description",
  "category": "Meals, Tools, Software, Office Expense, Employee Cost, Contractor Payment, Rent, Utilities, Internet/Phone, Vehicle, Marketing, Professional Fees, Insurance, Bank Fees, Travel, Income, Uncategorized",
  "subtotal": 0,
  "tax": 0,
  "total": 0,
  "currency": "CAD",
  "confidence": "high, medium, low"
}

Rules:
- Receipt/bill paid by user = expense.
- Invoice issued to client/customer = income.
- If unsure, use expense.
- If tax is missing, use 0.
- If category is unclear, use Uncategorized.
- Do not add explanations.
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
                ],
            }
        ],
    )

    content = response.choices[0].message.content

    try:
        return json.loads(content)
    except Exception:
        return {
            "transaction_type": "expense",
            "date": "",
            "name": "",
            "description": "",
            "category": "Uncategorized",
            "subtotal": 0,
            "tax": 0,
            "total": 0,
            "currency": "CAD",
            "confidence": "low",
        }
