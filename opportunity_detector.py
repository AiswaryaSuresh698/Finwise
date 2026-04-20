# core/opportunity_detector.py

from __future__ import annotations
import pandas as pd


def detect_opportunities(df: pd.DataFrame) -> list[dict]:
    """
    Detects simple tax-saving opportunities from enriched transaction data.
    """

    opportunities = []

    working_df = df.copy()
    expense_df = working_df[
        working_df["transaction_type"].astype(str).str.lower() == "expense"
    ].copy()

    # 1. Uncategorized expenses
    uncategorized = expense_df[expense_df["category"] == "Uncategorized"]
    if not uncategorized.empty:
        total_uncategorized = round(float(uncategorized["amount"].sum()), 2)
        opportunities.append({
            "type": "uncategorized_expenses",
            "title": "Uncategorized expenses may contain missed deductions",
            "estimated_amount": total_uncategorized,
            "estimated_tax_saving": round(total_uncategorized * 0.20, 2),
            "confidence": "medium",
            "action": "Review uncategorized expenses and assign business-related categories.",
            "transaction_count": int(len(uncategorized)),
        })

    # 2. Meals partial deduction reminder
    meals = expense_df[expense_df["category"] == "Meals"]
    if not meals.empty:
        total_meals = round(float(meals["amount"].sum()), 2)
        deductible_meals = round(total_meals * 0.50, 2)

        opportunities.append({
            "type": "meals_partial_deduction",
            "title": "Meals are only partially deductible",
            "estimated_amount": deductible_meals,
            "estimated_tax_saving": round(deductible_meals * 0.20, 2),
            "confidence": "high",
            "action": "Keep only business-related meals and maintain proper notes or context.",
            "transaction_count": int(len(meals)),
        })

    # 3. Internet/Phone partial allocation
    telecom = expense_df[expense_df["category"] == "Internet/Phone"]
    if not telecom.empty:
        total_telecom = round(float(telecom["amount"].sum()), 2)
        business_portion = round(total_telecom * 0.50, 2)

        opportunities.append({
            "type": "telecom_allocation",
            "title": "Internet and phone expenses may support partial business allocation",
            "estimated_amount": business_portion,
            "estimated_tax_saving": round(business_portion * 0.20, 2),
            "confidence": "medium",
            "action": "Allocate a reasonable business-use percentage for telecom costs.",
            "transaction_count": int(len(telecom)),
        })

    # 4. Vehicle partial allocation
    vehicle = expense_df[expense_df["category"] == "Vehicle"]
    if not vehicle.empty:
        total_vehicle = round(float(vehicle["amount"].sum()), 2)
        business_portion = round(total_vehicle * 0.40, 2)

        opportunities.append({
            "type": "vehicle_allocation",
            "title": "Vehicle expenses may support business-use deductions",
            "estimated_amount": business_portion,
            "estimated_tax_saving": round(business_portion * 0.20, 2),
            "confidence": "medium",
            "action": "Track business-use mileage or percentage for vehicle expenses.",
            "transaction_count": int(len(vehicle)),
        })

    # 5. Home office missing signal
    has_rent = not expense_df[expense_df["category"] == "Rent"].empty
    has_utilities = not expense_df[expense_df["category"] == "Utilities"].empty
    has_home_office = not expense_df[expense_df["category"] == "Home Office"].empty

    if (has_rent or has_utilities) and not has_home_office:
        opportunities.append({
            "type": "home_office_review",
            "title": "You may be missing a home office deduction review",
            "estimated_amount": 0.0,
            "estimated_tax_saving": 0.0,
            "confidence": "low",
            "action": "If you work from home, review whether part of rent and utilities may be business-related.",
            "transaction_count": 0,
        })

    # 6. Software recurring cost visibility
    software = expense_df[expense_df["category"] == "Software"]
    if not software.empty:
        total_software = round(float(software["amount"].sum()), 2)

        opportunities.append({
            "type": "software_review",
            "title": "Software expenses are being captured as deductible business costs",
            "estimated_amount": total_software,
            "estimated_tax_saving": round(total_software * 0.20, 2),
            "confidence": "high",
            "action": "Keep software subscriptions properly categorized to preserve full deduction treatment.",
            "transaction_count": int(len(software)),
        })

    return opportunities
