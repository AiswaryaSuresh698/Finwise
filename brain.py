# core/brain.py

from __future__ import annotations
import pandas as pd

from core.tax_engine import apply_tax_rules, calculate_tax_summary, get_category_summary
from core.opportunity_detector import detect_opportunities
from core.explainer import build_summary_text, build_user_friendly_opportunity_cards


def run_finwise_brain(categorized_df: pd.DataFrame) -> dict:
    """
    Runs Layers 3, 4, and 5:
    - tax rules engine
    - opportunity detector
    - explainer
    """

    enriched_df = apply_tax_rules(categorized_df)
    tax_summary = calculate_tax_summary(enriched_df)
    category_summary = get_category_summary(enriched_df)
    opportunities = detect_opportunities(enriched_df)
    summary_text = build_summary_text(tax_summary, opportunities)
    opportunity_cards = build_user_friendly_opportunity_cards(opportunities)

    return {
        "transactions": enriched_df,
        "tax_summary": tax_summary,
        "category_summary": category_summary,
        "opportunities": opportunities,
        "opportunity_cards": opportunity_cards,
        "summary_text": summary_text,
    }
