import pandas as pd
import re


def load_file(uploaded_file):
    name = uploaded_file.name.lower()

    if name.endswith(".csv"):
        return pd.read_csv(uploaded_file)
    elif name.endswith(".xlsx") or name.endswith(".xls"):
        return pd.read_excel(uploaded_file)
    else:
        raise ValueError("Unsupported file format")


def guess_column_mapping(columns):
    lowered = {c.lower(): c for c in columns}

    mapping = {}

    for c in columns:
        lc = c.lower()

        if "date" in lc and "date" not in mapping:
            mapping["date"] = c

        elif any(x in lc for x in ["description", "merchant", "details", "narration", "transaction"]) and "description" not in mapping:
            mapping["description"] = c

        elif "amount" in lc and "amount" not in mapping:
            mapping["amount"] = c

        elif any(x in lc for x in ["type", "transaction type"]) and "type" not in mapping:
            mapping["type"] = c

        elif "debit" in lc and "debit" not in mapping:
            mapping["debit"] = c

        elif "credit" in lc and "credit" not in mapping:
            mapping["credit"] = c

    return mapping


def normalize_transactions(df, mapping):
    out = pd.DataFrame()

    out["date"] = pd.to_datetime(df[mapping["date"]], errors="coerce")
    out["description"] = df[mapping["description"]].astype(str).fillna("")

    if mapping.get("amount"):
        out["amount"] = pd.to_numeric(df[mapping["amount"]], errors="coerce").fillna(0)

        if mapping.get("type"):
            out["transaction_type"] = (
                df[mapping["type"]].astype(str).str.strip().str.lower()
            )
            out["transaction_type"] = out["transaction_type"].replace({
                "dr": "expense",
                "debit": "expense",
                "cr": "income",
                "credit": "income"
            })
        else:
            out["transaction_type"] = out["amount"].apply(lambda x: "expense" if x < 0 else "income")
            out["amount"] = out["amount"].abs()

    else:
        debit_series = pd.to_numeric(df[mapping["debit"]], errors="coerce").fillna(0)
        credit_series = pd.to_numeric(df[mapping["credit"]], errors="coerce").fillna(0)

        out["amount"] = debit_series.where(debit_series > 0, credit_series)
        out["transaction_type"] = debit_series.apply(lambda x: "expense" if x > 0 else "income")

    out["amount"] = out["amount"].abs()
    out["notes"] = ""

    out = out.dropna(subset=["date", "description"])
    out = out.reset_index(drop=True)

    return out


def get_category_options():
    return [
        "Income",
        "Software",
        "Meals",
        "Travel",
        "Marketing",
        "Office Expense",
        "Internet/Phone",
        "Home Office",
        "Vehicle",
        "Professional Fees",
        "Insurance",
        "Bank Fees",
        "Training/Education",
        "Contractor Payments",
        "Rent",
        "Utilities",
        "Taxes Paid",
        "Uncategorized"
    ]


def categorize_transactions(df):
    category_rules = {
        "Software": [
            "adobe", "canva", "figma", "notion", "chatgpt", "openai", "slack",
            "zoom", "dropbox", "github", "microsoft", "google workspace"
        ],
        "Meals": [
            "starbucks", "uber eats", "doordash", "restaurant", "cafe", "tim hortons", "mcdonald"
        ],
        "Travel": [
            "air canada", "uber trip", "lyft", "airbnb", "expedia", "booking.com", "hotel"
        ],
        "Marketing": [
            "facebook ads", "meta ads", "google ads", "linkedin ads", "mailchimp", "convertkit"
        ],
        "Office Expense": [
            "staples", "office depot", "printer", "paper", "desk", "chair"
        ],
        "Internet/Phone": [
            "rogers", "bell", "telus", "fido", "videotron", "internet", "wireless", "mobile"
        ],
        "Professional Fees": [
            "lawyer", "legal", "accountant", "bookkeeper", "consulting fee"
        ],
        "Insurance": [
            "insurance", "policy"
        ],
        "Bank Fees": [
            "bank fee", "service charge", "monthly fee", "processing fee"
        ],
        "Training/Education": [
            "udemy", "coursera", "course", "training", "workshop"
        ],
        "Vehicle": [
            "gas", "fuel", "shell", "esso", "petro", "car wash", "parking"
        ],
        "Rent": [
            "rent", "lease"
        ],
        "Utilities": [
            "hydro", "electricity", "water", "utility"
        ],
        "Taxes Paid": [
            "cra", "tax payment", "gst", "hst"
        ]
    }

    categories = []
    confidences = []

    for _, row in df.iterrows():
        desc = str(row["description"]).lower()

        if row["transaction_type"] == "income":
            categories.append("Income")
            confidences.append("high")
            continue

        matched_category = "Uncategorized"
        confidence = "low"

        for category, keywords in category_rules.items():
            if any(keyword in desc for keyword in keywords):
                matched_category = category
                confidence = "high"
                break

        if matched_category == "Uncategorized":
            if re.search(r"subscription|saas|app|cloud", desc):
                matched_category = "Software"
                confidence = "medium"
            elif re.search(r"meal|lunch|dinner|coffee", desc):
                matched_category = "Meals"
                confidence = "medium"

        categories.append(matched_category)
        confidences.append(confidence)

    df["category"] = categories
    df["category_confidence"] = confidences
    return df
