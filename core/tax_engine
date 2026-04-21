# core/tax_engine.py

from __future__ import annotations
import pandas as pd
from core.tax_rules import TAX_RULES


def apply_tax_rules(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds deduction-related columns to a categorized transaction dataframe.
    Expected columns:
    - amount
    - transaction_type
    - category
    """

    working_df = df.copy()

    deductible_percents = []
    deductible_amounts = []
    rule_types = []
    rule_explanations = []

    for _, row in working_df.iterrows():
        category = row.get("category", "Uncategorized")
        transaction_type = str(row.get("transaction_type", "")).strip().lower()
        amount = float(row.get("amount", 0) or 0)

        rule = TAX_RULES.get(category, TAX_RULES["Uncategorized"])
        deductible_percent = rule["deductible_percent"]

        if transaction_type == "income":
            deductible_amount = 0.0
        else:
            deductible_amount = round(amount * (deductible_percent / 100), 2)

        deductible_percents.append(deductible_percent)
        deductible_amounts.append(deductible_amount)
        rule_types.append(rule["rule_type"])
        rule_explanations.append(rule["explanation"])

    working_df["deductible_percent"] = deductible_percents
    working_df["deductible_amount"] = deductible_amounts
    working_df["rule_type"] = rule_types
    working_df["rule_explanation"] = rule_explanations

    return working_df


def calculate_tax_summary(df: pd.DataFrame) -> dict:
    """
    Produces a simple summary from the enriched transaction dataframe.
    """

    working_df = df.copy()

    income_mask = working_df["transaction_type"].astype(str).str.lower() == "income"
    expense_mask = working_df["transaction_type"].astype(str).str.lower() == "expense"

    total_income = float(working_df.loc[income_mask, "amount"].sum())
    total_expense = float(working_df.loc[expense_mask, "amount"].sum())
    total_deductible = float(working_df["deductible_amount"].sum())

    taxable_income = max(total_income - total_deductible, 0)

    # Placeholder estimate for MVP.
    # Later you can replace this with province + bracket based logic.
    estimated_tax = round(taxable_income * 0.20, 2)

    return {
        "total_income": round(total_income, 2),
        "total_expense": round(total_expense, 2),
        "total_deductible": round(total_deductible, 2),
        "taxable_income": round(taxable_income, 2),
        "estimated_tax": estimated_tax,
    }


def get_category_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns category-level totals for reporting.
    """

    working_df = df.copy()

    summary = (
        working_df.groupby(["category", "transaction_type"], dropna=False)
        .agg(
            total_amount=("amount", "sum"),
            total_deductible=("deductible_amount", "sum"),
            row_count=("amount", "count"),
        )
        .reset_index()
        .sort_values(["transaction_type", "total_amount"], ascending=[True, False])
    )

    return summary
