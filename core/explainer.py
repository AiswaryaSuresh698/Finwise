# core/explainer.py

from __future__ import annotations


def build_summary_text(tax_summary: dict, opportunities: list[dict]) -> str:
    """
    Builds a plain-language explanation string for chat or UI.
    """

    lines = []

    lines.append("Here is your FinWise summary:")
    lines.append(f"- Total income: ${tax_summary['total_income']:.2f}")
    lines.append(f"- Total expenses: ${tax_summary['total_expense']:.2f}")
    lines.append(f"- Total deductible expenses: ${tax_summary['total_deductible']:.2f}")
    lines.append(f"- Estimated taxable income: ${tax_summary['taxable_income']:.2f}")
    lines.append(f"- Estimated tax: ${tax_summary['estimated_tax']:.2f}")
    lines.append("")

    if opportunities:
        lines.append("Potential tax-saving opportunities:")
        for idx, opp in enumerate(opportunities, start=1):
            lines.append(
                f"{idx}. {opp['title']} | "
                f"Possible tax saving: ${opp['estimated_tax_saving']:.2f} | "
                f"Action: {opp['action']}"
            )
    else:
        lines.append("No major tax-saving opportunities detected yet.")

    return "\n".join(lines)


def build_user_friendly_opportunity_cards(opportunities: list[dict]) -> list[dict]:
    """
    Optional helper to make opportunity data easier to show in the UI.
    """

    cards = []

    for opp in opportunities:
        cards.append({
            "title": opp["title"],
            "subtitle": f"Confidence: {opp['confidence'].title()}",
            "tax_saving_text": f"${opp['estimated_tax_saving']:.2f}",
            "action": opp["action"],
            "type": opp["type"],
        })

    return cards
