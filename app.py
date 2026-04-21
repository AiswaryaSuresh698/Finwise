import streamlit as st
import pandas as pd
from utils import (
    load_file,
    guess_column_mapping,
    normalize_transactions,
    categorize_transactions,
    get_category_options
)

st.set_page_config(page_title="FinWise Tax", layout="wide")

st.title("FinWise Tax")
st.caption("Upload transactions and review categorized expenses")

# -----------------------------
# Session state setup
# -----------------------------
if "raw_df" not in st.session_state:
    st.session_state.raw_df = None

if "mapped_df" not in st.session_state:
    st.session_state.mapped_df = None

if "categorized_df" not in st.session_state:
    st.session_state.categorized_df = None

if "column_mapping" not in st.session_state:
    st.session_state.column_mapping = {}

if "current_screen" not in st.session_state:
    st.session_state.current_screen = "Screen 1"

if "finwise_result" not in st.session_state:
    st.session_state.finwise_result = None

# -----------------------------
# Sidebar navigation
# -----------------------------
screen = st.sidebar.radio(
    "Go to",
    [
        "Screen 1 - Upload",
        "Screen 2 - Review Categories",
        "Screen 3 - Tax Summary"
    ]
)
)

# -----------------------------
# SCREEN 1 - UPLOAD + MAPPING
# -----------------------------
if screen == "Screen 1 - Upload":
    st.session_state.current_screen = "Screen 1"
    st.subheader("Screen 1: Upload Transactions")

    uploaded_file = st.file_uploader(
        "Upload CSV or Excel file",
        type=["csv", "xlsx", "xls"]
    )

    if uploaded_file:
        try:
            raw_df = load_file(uploaded_file)
            st.session_state.raw_df = raw_df

            st.success("File uploaded successfully.")
            st.write("### Raw data preview")
            st.dataframe(raw_df.head(20), use_container_width=True)

            st.write("### Map your columns")
            guessed = guess_column_mapping(raw_df.columns.tolist())

            cols = raw_df.columns.tolist()
            select_options = ["-- Select --"] + cols

            col1, col2 = st.columns(2)
            with col1:
                date_col = st.selectbox(
                    "Date column",
                    select_options,
                    index=select_options.index(guessed.get("date", "-- Select --"))
                    if guessed.get("date", "-- Select --") in select_options else 0
                )
                description_col = st.selectbox(
                    "Description / Merchant column",
                    select_options,
                    index=select_options.index(guessed.get("description", "-- Select --"))
                    if guessed.get("description", "-- Select --") in select_options else 0
                )
                amount_col = st.selectbox(
                    "Amount column",
                    select_options,
                    index=select_options.index(guessed.get("amount", "-- Select --"))
                    if guessed.get("amount", "-- Select --") in select_options else 0
                )

            with col2:
                income_expense_col = st.selectbox(
                    "Type column (optional: income / expense)",
                    select_options,
                    index=select_options.index(guessed.get("type", "-- Select --"))
                    if guessed.get("type", "-- Select --") in select_options else 0
                )
                debit_col = st.selectbox(
                    "Debit column (optional)",
                    select_options,
                    index=select_options.index(guessed.get("debit", "-- Select --"))
                    if guessed.get("debit", "-- Select --") in select_options else 0
                )
                credit_col = st.selectbox(
                    "Credit column (optional)",
                    select_options,
                    index=select_options.index(guessed.get("credit", "-- Select --"))
                    if guessed.get("credit", "-- Select --") in select_options else 0
                )

            mapping = {
                "date": None if date_col == "-- Select --" else date_col,
                "description": None if description_col == "-- Select --" else description_col,
                "amount": None if amount_col == "-- Select --" else amount_col,
                "type": None if income_expense_col == "-- Select --" else income_expense_col,
                "debit": None if debit_col == "-- Select --" else debit_col,
                "credit": None if credit_col == "-- Select --" else credit_col,
            }

            st.session_state.column_mapping = mapping

            if st.button("Normalize transactions", type="primary"):
                required_missing = [
                    key for key in ["date", "description"]
                    if not mapping.get(key)
                ]

                if required_missing:
                    st.error(f"Missing required mapping: {', '.join(required_missing)}")
                elif not mapping.get("amount") and not (mapping.get("debit") and mapping.get("credit")):
                    st.error("Provide either Amount column OR both Debit and Credit columns.")
                else:
                    normalized_df = normalize_transactions(raw_df, mapping)
                    st.session_state.mapped_df = normalized_df

                    st.success("Transactions normalized successfully.")
                    st.write("### Normalized transaction preview")
                    st.dataframe(normalized_df.head(20), use_container_width=True)

                    st.info("Now move to Screen 2 to review categories.")

        except Exception as e:
            st.error(f"Error reading file: {e}")

# -----------------------------
# SCREEN 2 - CATEGORY REVIEW
# -----------------------------
elif screen == "Screen 2 - Review Categories":
    st.session_state.current_screen = "Screen 2"
    st.subheader("Screen 2: Review Categorized Transactions")

    if st.session_state.mapped_df is None:
        st.warning("Please complete Screen 1 first.")
        st.stop()

    if st.session_state.categorized_df is None:
        categorized_df = categorize_transactions(st.session_state.mapped_df.copy())
        st.session_state.categorized_df = categorized_df

    df = st.session_state.categorized_df.copy()

    st.write("### Filters")
    f1, f2, f3 = st.columns(3)

    with f1:
        type_filter = st.selectbox("Transaction Type", ["All", "income", "expense"])
    with f2:
        confidence_filter = st.selectbox("Confidence", ["All", "high", "medium", "low"])
    with f3:
        search_text = st.text_input("Search description")

    filtered_df = df.copy()

    if type_filter != "All":
        filtered_df = filtered_df[filtered_df["transaction_type"].str.lower() == type_filter]

    if confidence_filter != "All":
        filtered_df = filtered_df[filtered_df["category_confidence"].str.lower() == confidence_filter]

    if search_text.strip():
        filtered_df = filtered_df[
            filtered_df["description"].astype(str).str.contains(search_text, case=False, na=False)
        ]

    st.write("### Summary")
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Rows", len(filtered_df))
    s2.metric("Income", f"{filtered_df.loc[filtered_df['transaction_type']=='income', 'amount'].sum():,.2f}")
    s3.metric("Expense", f"{filtered_df.loc[filtered_df['transaction_type']=='expense', 'amount'].sum():,.2f}")
    s4.metric("Uncategorized", int((filtered_df["category"] == "Uncategorized").sum()))

    st.write("### Review and edit categories")

    category_options = get_category_options()

    editable_df = filtered_df[
        ["date", "description", "amount", "transaction_type", "category", "category_confidence", "notes"]
    ].copy()

    edited_df = st.data_editor(
        editable_df,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "date": st.column_config.DateColumn("Date"),
            "description": st.column_config.TextColumn("Description", width="large"),
            "amount": st.column_config.NumberColumn("Amount", format="%.2f"),
            "transaction_type": st.column_config.SelectboxColumn(
                "Transaction Type",
                options=["income", "expense"]
            ),
            "category": st.column_config.SelectboxColumn(
                "Category",
                options=category_options
            ),
            "category_confidence": st.column_config.SelectboxColumn(
                "Confidence",
                options=["high", "medium", "low"]
            ),
            "notes": st.column_config.TextColumn("Notes", width="medium"),
        },
        key="category_editor"
    )

    if st.button("Save category changes", type="primary"):
        base_df = st.session_state.categorized_df.copy()

        update_cols = ["date", "description", "amount", "transaction_type"]
        merged = base_df.merge(
            edited_df,
            on=update_cols,
            how="left",
            suffixes=("", "_edited")
        )

        for col in ["category", "category_confidence", "notes"]:
            edited_col = f"{col}_edited"
            if edited_col in merged.columns:
                merged[col] = merged[edited_col].combine_first(merged[col])
                merged.drop(columns=[edited_col], inplace=True)

        st.session_state.categorized_df = merged
        st.success("Category updates saved.")

    st.write("### Category distribution")
    cat_summary = (
        filtered_df.groupby("category", dropna=False)["amount"]
        .sum()
        .reset_index()
        .sort_values("amount", ascending=False)
    )
    st.dataframe(cat_summary, use_container_width=True)

    csv = st.session_state.categorized_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download categorized transactions CSV",
        data=csv,
        file_name="categorized_transactions.csv",
        mime="text/csv"
    )

# -----------------------------
# SCREEN 3 - TAX SUMMARY
# -----------------------------
elif screen == "Screen 3 - Tax Summary":
    st.subheader("Screen 3: Tax Summary")

    if st.session_state.categorized_df is None:
        st.warning("Please complete Screen 1 and Screen 2 first.")
        st.stop()

    from core.brain import run_finwise_brain

    col_a, col_b = st.columns([1, 1])

    with col_a:
        if st.button("Run FinWise Analysis", type="primary", use_container_width=True):
            result = run_finwise_brain(st.session_state.categorized_df)
            st.session_state.finwise_result = result
            st.success("FinWise analysis completed.")

    with col_b:
        if st.button("Refresh Analysis", use_container_width=True):
            result = run_finwise_brain(st.session_state.categorized_df)
            st.session_state.finwise_result = result
            st.success("Analysis refreshed.")

    if st.session_state.finwise_result is None:
        st.info("Click 'Run FinWise Analysis' to generate your tax summary.")
        st.stop()

    result = st.session_state.finwise_result

    tax_summary = result["tax_summary"]
    category_summary = result["category_summary"]
    transactions = result["transactions"]
    opportunities = result["opportunities"]
    summary_text = result["summary_text"]

    # -----------------------------
    # SUMMARY CARDS
    # -----------------------------
    st.write("## Tax Summary")

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Total Income", f"${tax_summary['total_income']:,.2f}")
    m2.metric("Total Expenses", f"${tax_summary['total_expense']:,.2f}")
    m3.metric("Deductible Expenses", f"${tax_summary['total_deductible']:,.2f}")
    m4.metric("Taxable Income", f"${tax_summary['taxable_income']:,.2f}")
    m5.metric("Estimated Tax", f"${tax_summary['estimated_tax']:,.2f}")

    # -----------------------------
    # OPPORTUNITIES
    # -----------------------------
    st.write("## Tax-Saving Opportunities")

    if opportunities:
        for opp in opportunities:
            with st.container():
                st.markdown(f"### {opp['title']}")
                c1, c2, c3 = st.columns(3)
                c1.metric("Possible Tax Saving", f"${opp['estimated_tax_saving']:,.2f}")
                c2.metric("Estimated Amount", f"${opp['estimated_amount']:,.2f}")
                c3.metric("Confidence", opp["confidence"].title())

                st.write(f"**Action:** {opp['action']}")
                if "transaction_count" in opp:
                    st.caption(f"Related transactions: {opp['transaction_count']}")
                st.divider()
    else:
        st.success("No major tax-saving opportunities detected yet.")

    # -----------------------------
    # CATEGORY SUMMARY
    # -----------------------------
    st.write("## Category Summary")
    st.dataframe(category_summary, use_container_width=True)

    # -----------------------------
    # DETAILED TRANSACTIONS
    # -----------------------------
    st.write("## Detailed Transactions with Tax Treatment")

    display_cols = [
        "date",
        "description",
        "amount",
        "transaction_type",
        "category",
        "deductible_percent",
        "deductible_amount",
        "rule_type",
        "rule_explanation"
    ]

    available_cols = [col for col in display_cols if col in transactions.columns]

    st.dataframe(
        transactions[available_cols],
        use_container_width=True
    )

    # -----------------------------
    # EXPLANATION
    # -----------------------------
    st.write("## FinWise Explanation")
    st.text_area(
        "Summary",
        value=summary_text,
        height=250
    )

    # -----------------------------
    # DOWNLOAD ENRICHED CSV
    # -----------------------------
    csv = transactions.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download Tax-Enriched Transactions CSV",
        data=csv,
        file_name="finwise_tax_summary.csv",
        mime="text/csv"
    )
