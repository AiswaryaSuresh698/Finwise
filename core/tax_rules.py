# core/tax_rules.py

TAX_RULES = {
    "Income": {
        "deductible_percent": 0,
        "rule_type": "income",
        "explanation": "Income is not deductible."
    },
    "Software": {
        "deductible_percent": 100,
        "rule_type": "full",
        "explanation": "Software used for business is generally fully deductible."
    },
    "Meals": {
        "deductible_percent": 50,
        "rule_type": "partial",
        "explanation": "Business meals are generally 50% deductible."
    },
    "Travel": {
        "deductible_percent": 100,
        "rule_type": "full",
        "explanation": "Business travel is generally fully deductible."
    },
    "Marketing": {
        "deductible_percent": 100,
        "rule_type": "full",
        "explanation": "Advertising and marketing expenses are generally fully deductible."
    },
    "Office Expense": {
        "deductible_percent": 100,
        "rule_type": "full",
        "explanation": "Office expenses used for business are generally fully deductible."
    },
    "Internet/Phone": {
        "deductible_percent": 50,
        "rule_type": "partial",
        "explanation": "Internet and phone expenses may be partially deductible based on business use."
    },
    "Home Office": {
        "deductible_percent": 30,
        "rule_type": "partial",
        "explanation": "Home office expenses are usually allocated based on business use."
    },
    "Vehicle": {
        "deductible_percent": 40,
        "rule_type": "partial",
        "explanation": "Vehicle expenses are generally deductible only for the business-use portion."
    },
    "Professional Fees": {
        "deductible_percent": 100,
        "rule_type": "full",
        "explanation": "Professional fees related to business are generally deductible."
    },
    "Insurance": {
        "deductible_percent": 100,
        "rule_type": "full",
        "explanation": "Business insurance is generally deductible."
    },
    "Bank Fees": {
        "deductible_percent": 100,
        "rule_type": "full",
        "explanation": "Business banking fees are generally deductible."
    },
    "Training/Education": {
        "deductible_percent": 100,
        "rule_type": "full",
        "explanation": "Training directly related to the business may be deductible."
    },
    "Contractor Payments": {
        "deductible_percent": 100,
        "rule_type": "full",
        "explanation": "Contractor payments related to business operations are generally deductible."
    },
    "Rent": {
        "deductible_percent": 100,
        "rule_type": "full",
        "explanation": "Business rent is generally deductible."
    },
    "Utilities": {
        "deductible_percent": 100,
        "rule_type": "full",
        "explanation": "Business utility expenses are generally deductible."
    },
    "Taxes Paid": {
        "deductible_percent": 0,
        "rule_type": "non_deductible",
        "explanation": "Tax payments should be reviewed carefully before deduction treatment."
    },
    "Uncategorized": {
        "deductible_percent": 0,
        "rule_type": "unknown",
        "explanation": "This transaction needs review before deduction treatment."
    }
}
