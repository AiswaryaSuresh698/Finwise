# core/ai_helper.py

from __future__ import annotations
import json
from openai import OpenAI


def get_openai_client(api_key: str) -> OpenAI:
    return OpenAI(api_key=api_key)


def build_finwise_context(finwise_result: dict, max_transactions: int = 25) -> str:
    tax_summary = finwise_result.get("tax_summary", {})
    opportunities = finwise_result.get("opportunities", [])
    category_summary_df = finwise_result.get("category_summary")
    transactions_df = finwise_result.get("transactions")

    category_summary = []
    if category_summary_df is not None:
        try:
            category_summary = category_summary_df.to_dict(orient="records")
        except Exception:
            category_summary = []

    top_transactions = []
    if transactions_df is not None:
        try:
            trimmed = transactions_df.head(max_transactions)
            cols = [
                c for c in [
                    "date",
                    "description",
                    "amount",
                    "transaction_type",
                    "category",
                    "deductible_percent",
                    "deductible_amount",
                ]
                if c in trimmed.columns
            ]
            top_transactions = trimmed[cols].to_dict(orient="records")
        except Exception:
            top_transactions = []

    payload = {
        "tax_summary": tax_summary,
        "opportunities": opportunities,
        "category_summary": category_summary,
        "sample_transactions": top_transactions,
    }

    return json.dumps(payload, default=str, indent=2)


def generate_ai_explanation(
    client: OpenAI,
    finwise_result: dict,
    user_type: str = "Canadian freelancer",
    model: str = "gpt-4.1-mini",
) -> str:
    context = build_finwise_context(finwise_result)

    system_prompt = (
        "You are FinWise AI, a financial tax-assistant for freelancers and small businesses. "
        "You explain results clearly and simply. "
        "Use the structured results provided. "
        "Do not invent numbers. "
        "Do not claim legal certainty. "
        "Focus on what the user should review, what may save tax, and what to do next."
    )

    user_prompt = f"""
The user is a {user_type}.

Explain the FinWise analysis in simple language.

Please provide:
1. A short plain-English summary
2. Top 3 tax-saving opportunities
3. Key caution points
4. A practical next-step checklist

Use this structured context:
{context}
"""

    response = client.chat.completions.create(
        model=model,
        temperature=0.2,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    return response.choices[0].message.content or ""


def answer_finwise_chat(
    client: OpenAI,
    finwise_result: dict,
    user_question: str,
    chat_history: list[dict] | None = None,
    model: str = "gpt-4.1-mini",
) -> str:
    context = build_finwise_context(finwise_result)

    system_prompt = (
        "You are FinWise AI, a helpful tax and expense-analysis assistant for Canadian freelancers. "
        "Answer using the provided FinWise results first. "
        "Be concise, practical, and clear. "
        "If the data does not support a precise answer, say that the current uploaded data does not show enough detail. "
        "Do not invent transactions or savings."
    )

    messages = [{"role": "system", "content": system_prompt}]

    messages.append({
        "role": "user",
        "content": f"Here is the FinWise analysis context:\n{context}"
    })

    if chat_history:
        for item in chat_history[-8:]:
            if item.get("role") in {"user", "assistant"} and item.get("content"):
                messages.append({
                    "role": item["role"],
                    "content": item["content"]
                })

    messages.append({
        "role": "user",
        "content": user_question
    })

    response = client.chat.completions.create(
        model=model,
        temperature=0.2,
        messages=messages,
    )

    return response.choices[0].message.content or ""
