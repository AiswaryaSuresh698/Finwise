import os
import streamlit as st
import pandas as pd

from utils import (
    load_file,
    guess_column_mapping,
    normalize_transactions,
    categorize_transactions,
    get_category_options
)

from core.brain import run_finwise_brain


st.set_page_config(page_title="FinWise Tax", layout="wide")

st.title("FinWise Tax")
st.caption("Upload transactions, review categories, analyze tax savings, and ask AI questions.")

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

if "finwise_ai_explanation" not in st.session_state:
    st.session_state.finwise_ai_explanation = None

if "finwise_chat_history" not in st.session_state:
    st.session_state.finwise_chat_history = []

if "bill_entries" not in st.session_state:
    st.session_state.bill_entries = []
# -----------------------------
# Sidebar navigation
# -----------------------------
screen = st.sidebar.radio(
    "Go to",
    [
        "Screen 1 - Upload",
        "Screen 2 - Review Categories",
        "Screen 3 - Tax Summary",
        "Screen 4 - AI Assistant",
        "Screen 5 - Filing Guide",
        "Screen 6 - Bill Scanner"
    ]
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

                    # Optional safety: add transaction_id if missing
                    if "transaction_id" not in normalized_df.columns:
                        normalized_df = normalized_df.reset_index(drop=True)
                        normalized_df["transaction_id"] = range(1, len(normalized_df) + 1)

                    st.session_state.mapped_df = normalized_df
                    st.session_state.categorized_df = None
                    st.session_state.finwise_result = None
                    st.session_state.finwise_ai_explanation = None
                    st.session_state.finwise_chat_history = []

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

        if "transaction_id" not in categorized_df.columns:
            categorized_df = categorized_df.reset_index(drop=True)
            categorized_df["transaction_id"] = range(1, len(categorized_df) + 1)

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
        filtered_df = filtered_df[
            filtered_df["transaction_type"].astype(str).str.lower() == type_filter
        ]

    if confidence_filter != "All":
        filtered_df = filtered_df[
            filtered_df["category_confidence"].astype(str).str.lower() == confidence_filter
        ]

    if search_text.strip():
        filtered_df = filtered_df[
            filtered_df["description"].astype(str).str.contains(search_text, case=False, na=False)
        ]

    st.write("### Summary")
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Rows", len(filtered_df))
    s2.metric(
        "Income",
        f"{filtered_df.loc[filtered_df['transaction_type'].astype(str).str.lower() == 'income', 'amount'].sum():,.2f}"
    )
    s3.metric(
        "Expense",
        f"{filtered_df.loc[filtered_df['transaction_type'].astype(str).str.lower() == 'expense', 'amount'].sum():,.2f}"
    )
    s4.metric("Uncategorized", int((filtered_df["category"] == "Uncategorized").sum()))

    st.write("### Review and edit categories")

    category_options = get_category_options()

    editor_columns = [
        c for c in [
            "transaction_id",
            "date",
            "description",
            "amount",
            "transaction_type",
            "category",
            "category_confidence",
            "notes"
        ] if c in filtered_df.columns
    ]

    editable_df = filtered_df[editor_columns].copy()

    edited_df = st.data_editor(
        editable_df,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "transaction_id": st.column_config.NumberColumn("Transaction ID", disabled=True),
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

        if "transaction_id" in base_df.columns and "transaction_id" in edited_df.columns:
            base_df = base_df.set_index("transaction_id")
            edited_base = edited_df.set_index("transaction_id")

            for col in ["transaction_type", "category", "category_confidence", "notes"]:
                if col in edited_base.columns and col in base_df.columns:
                    base_df.loc[edited_base.index, col] = edited_base[col]

            st.session_state.categorized_df = base_df.reset_index()
        else:
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

        st.session_state.finwise_result = None
        st.session_state.finwise_ai_explanation = None
        st.session_state.finwise_chat_history = []
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
    st.session_state.current_screen = "Screen 3"
    st.subheader("Screen 3: Tax Summary")

    if st.session_state.categorized_df is None:
        st.warning("Please complete Screen 1 and Screen 2 first.")
        st.stop()

    col_a, col_b = st.columns([1, 1])

    with col_a:
        if st.button("Run FinWise Analysis", type="primary", use_container_width=True):
            result = run_finwise_brain(st.session_state.categorized_df)
            st.session_state.finwise_result = result
            st.session_state.finwise_ai_explanation = None
            st.session_state.finwise_chat_history = []
            st.success("FinWise analysis completed.")

    with col_b:
        if st.button("Refresh Analysis", use_container_width=True):
            result = run_finwise_brain(st.session_state.categorized_df)
            st.session_state.finwise_result = result
            st.session_state.finwise_ai_explanation = None
            st.session_state.finwise_chat_history = []
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

    st.write("## Tax Summary")

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Total Income", f"${tax_summary['total_income']:,.2f}")
    m2.metric("Total Expenses", f"${tax_summary['total_expense']:,.2f}")
    m3.metric("Deductible Expenses", f"${tax_summary['total_deductible']:,.2f}")
    m4.metric("Taxable Income", f"${tax_summary['taxable_income']:,.2f}")
    m5.metric("Estimated Tax", f"${tax_summary['estimated_tax']:,.2f}")

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

    st.write("## Category Summary")
    st.dataframe(category_summary, use_container_width=True)

    st.write("## Detailed Transactions with Tax Treatment")

    display_cols = [
        "transaction_id",
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

    st.dataframe(transactions[available_cols], use_container_width=True)

    st.write("## FinWise Explanation")
    st.text_area(
        "Summary",
        value=summary_text,
        height=250
    )

    csv = transactions.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download Tax-Enriched Transactions CSV",
        data=csv,
        file_name="finwise_tax_summary.csv",
        mime="text/csv"
    )


# -----------------------------
# SCREEN 4 - AI ASSISTANT
# -----------------------------
elif screen == "Screen 4 - AI Assistant":
    st.session_state.current_screen = "Screen 4"
    st.subheader("Screen 4: AI Explanation & Ask FinWise")

    if st.session_state.finwise_result is None:
        st.warning("Please complete Screen 3 and run FinWise analysis first.")
        st.stop()

    from core.ai_helper import (
        get_openai_client,
        generate_ai_explanation,
        answer_finwise_chat
    )

    api_key = None

    try:
        api_key = st.secrets["OPENAI_API_KEY"]
    except Exception:
        api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        st.error("OpenAI API key not found. Add OPENAI_API_KEY to Streamlit secrets or environment variables.")
        st.stop()

    client = get_openai_client(api_key)
    result = st.session_state.finwise_result

    tab1, tab2 = st.tabs(["AI Explanation", "Ask FinWise"])

    with tab1:
        st.write("Generate a simple explanation of your tax summary and savings opportunities.")

        col1, col2 = st.columns([1, 1])

        with col1:
            if st.button("Generate AI Explanation", type="primary", use_container_width=True):
                with st.spinner("Generating AI explanation..."):
                    explanation = generate_ai_explanation(
                        client=client,
                        finwise_result=result,
                        user_type="Canadian freelancer"
                    )
                    st.session_state.finwise_ai_explanation = explanation

        with col2:
            if st.button("Regenerate Explanation", use_container_width=True):
                with st.spinner("Refreshing explanation..."):
                    explanation = generate_ai_explanation(
                        client=client,
                        finwise_result=result,
                        user_type="Canadian freelancer"
                    )
                    st.session_state.finwise_ai_explanation = explanation

        if st.session_state.finwise_ai_explanation:
            st.write("### AI Explanation")
            st.markdown(st.session_state.finwise_ai_explanation)
        else:
            st.info("Click 'Generate AI Explanation' to create a summary.")

    with tab2:
        st.write("Ask questions about your uploaded transactions, deductions, and tax-saving opportunities.")

        for msg in st.session_state.finwise_chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        user_question = st.chat_input("Ask FinWise something...")

        if user_question:
            st.session_state.finwise_chat_history.append({
                "role": "user",
                "content": user_question
            })

            with st.chat_message("user"):
                st.markdown(user_question)

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    answer = answer_finwise_chat(
                        client=client,
                        finwise_result=result,
                        user_question=user_question,
                        chat_history=st.session_state.finwise_chat_history,
                    )
                    st.markdown(answer)

            st.session_state.finwise_chat_history.append({
                "role": "assistant",
                "content": answer
            })

        col_clear1, col_clear2 = st.columns([1, 1])

        with col_clear1:
            if st.button("Clear Chat"):
                st.session_state.finwise_chat_history = []
                st.rerun()

        with col_clear2:
            if st.button("Clear AI Explanation"):
                st.session_state.finwise_ai_explanation = None
                st.rerun()

# -----------------------------
# SCREEN 5 - FILING GUIDE
# -----------------------------
elif screen == "Screen 5 - Filing Guide":
    st.session_state.current_screen = "Screen 5"
    st.subheader("Screen 5: Tax Filing Guide")

    if st.session_state.finwise_result is None:
        st.warning("Please complete Screen 3 and run FinWise analysis first.")
        st.stop()

    result = st.session_state.finwise_result
    tax_summary = result["tax_summary"]
    category_summary = result["category_summary"]
    transactions = result["transactions"]

    st.write("Use this screen to prepare values for tax filing tools like Wealthsimple Tax or TurboTax.")

    # -----------------------------
    # TOP SUMMARY
    # -----------------------------
    st.write("## Filing Summary")

    a1, a2, a3, a4 = st.columns(4)
    a1.metric("Business Income", f"${tax_summary['total_income']:,.2f}")
    a2.metric("Total Expenses", f"${tax_summary['total_expense']:,.2f}")
    a3.metric("Deductible Expenses", f"${tax_summary['total_deductible']:,.2f}")
    a4.metric("Estimated Net Income", f"${tax_summary['taxable_income']:,.2f}")

    # -----------------------------
    # TAX SOFTWARE SELECTION
    # -----------------------------
    st.write("## Select Filing Tool")
    filing_tool = st.selectbox(
        "Choose where you plan to file",
        ["Wealthsimple Tax", "TurboTax", "General Filing Format"]
    )

    # -----------------------------
    # CATEGORY MAPPING LOGIC
    # -----------------------------
    filing_mapping = {
        "Income": "Business Income",
        "Software": "Office Expenses / Software",
        "Meals": "Meals & Entertainment",
        "Travel": "Travel Expenses",
        "Marketing": "Advertising / Marketing",
        "Office Expense": "Office Expenses",
        "Internet/Phone": "Utilities / Telephone / Internet",
        "Home Office": "Business Use of Home",
        "Vehicle": "Motor Vehicle Expenses",
        "Professional Fees": "Professional Fees",
        "Insurance": "Insurance",
        "Bank Fees": "Bank Charges / Fees",
        "Training/Education": "Training / Education",
        "Contractor Payments": "Subcontractor / Contract Labour",
        "Rent": "Rent",
        "Utilities": "Utilities",
        "Taxes Paid": "Review Manually",
        "Uncategorized": "Review Manually"
    }

    working_summary = category_summary.copy()

    if "transaction_type" in working_summary.columns:
        working_summary = working_summary[
            working_summary["transaction_type"].astype(str).str.lower() == "expense"
        ].copy()

    if "total_deductible" not in working_summary.columns:
        st.error("Category summary does not contain total_deductible.")
        st.stop()

    working_summary["filing_field"] = working_summary["category"].map(filing_mapping).fillna("Review Manually")

    filing_table = (
        working_summary.groupby(["filing_field"], dropna=False)
        .agg(
            total_deductible=("total_deductible", "sum"),
            source_categories=("category", lambda x: ", ".join(sorted(set(map(str, x)))))
        )
        .reset_index()
        .sort_values("total_deductible", ascending=False)
    )

    filing_table["total_deductible"] = filing_table["total_deductible"].round(2)

    # -----------------------------
    # WHAT TO ENTER TABLE
    # -----------------------------
    st.write(f"## What to Enter in {filing_tool}")

    st.dataframe(
        filing_table.rename(columns={
            "filing_field": "Tax Software Field",
            "total_deductible": "Amount to Enter",
            "source_categories": "Comes From"
        }),
        use_container_width=True
    )

    # -----------------------------
    # STEP-BY-STEP GUIDE
    # -----------------------------
    st.write("## Step-by-Step Filing Guide")

    step_lines = []
    step_lines.append(f"1. Open {filing_tool}.")
    step_lines.append("2. Go to the self-employment or business income section.")
    step_lines.append(f"3. Enter Business Income = ${tax_summary['total_income']:,.2f}.")
    step_lines.append("4. Enter the deductible expense values below:")
    for _, row in filing_table.iterrows():
        if float(row["total_deductible"]) > 0:
            step_lines.append(f"   - {row['filing_field']}: ${row['total_deductible']:,.2f}")
    step_lines.append(f"5. Estimated net income after deductions: ${tax_summary['taxable_income']:,.2f}.")
    step_lines.append("6. Review manually flagged items such as Uncategorized or Taxes Paid before filing.")

    for line in step_lines:
        st.write(line)

    # -----------------------------
    # COPY/PASTE BLOCK
    # -----------------------------
    st.write("## Copy/Paste Filing Notes")

    filing_text_lines = []
    filing_text_lines.append(f"Filing Tool: {filing_tool}")
    filing_text_lines.append("")
    filing_text_lines.append(f"Business Income: ${tax_summary['total_income']:,.2f}")
    filing_text_lines.append(f"Total Expenses: ${tax_summary['total_expense']:,.2f}")
    filing_text_lines.append(f"Deductible Expenses: ${tax_summary['total_deductible']:,.2f}")
    filing_text_lines.append(f"Estimated Net Income: ${tax_summary['taxable_income']:,.2f}")
    filing_text_lines.append("")
    filing_text_lines.append("Enter these deductible amounts:")
    for _, row in filing_table.iterrows():
        if float(row["total_deductible"]) > 0:
            filing_text_lines.append(f"- {row['filing_field']}: ${row['total_deductible']:,.2f}")
    filing_text_lines.append("")
    filing_text_lines.append("Review manually:")
    manual_review_rows = filing_table[filing_table["filing_field"] == "Review Manually"]
    if not manual_review_rows.empty:
        for _, row in manual_review_rows.iterrows():
            filing_text_lines.append(f"- {row['Comes From'] if 'Comes From' in row else row['source_categories']}")
    else:
        filing_text_lines.append("- No manually flagged categories")

    filing_text = "\n".join(filing_text_lines)

    st.text_area(
        "Prepared Filing Notes",
        value=filing_text,
        height=300
    )

    # -----------------------------
    # DOWNLOAD BUTTONS
    # -----------------------------
    filing_csv = filing_table.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download Filing Guide CSV",
        data=filing_csv,
        file_name="finwise_filing_guide.csv",
        mime="text/csv"
    )

    filing_text_bytes = filing_text.encode("utf-8")
    st.download_button(
        "Download Filing Notes TXT",
        data=filing_text_bytes,
        file_name="finwise_filing_notes.txt",
        mime="text/plain"
    )

    # -----------------------------
    # OPTIONAL DETAIL VIEW
    # -----------------------------
    with st.expander("Show detailed transactions behind filing guide"):
        display_cols = [
            "transaction_id",
            "date",
            "description",
            "amount",
            "transaction_type",
            "category",
            "deductible_percent",
            "deductible_amount"
        ]
        available_cols = [col for col in display_cols if col in transactions.columns]
        st.dataframe(transactions[available_cols], use_container_width=True)

# -----------------------------
# SCREEN 6 - BILL SCANNER
# -----------------------------
elif screen == "Screen 6 - Bill Scanner":
    st.subheader("Screen 6: Bill / Receipt Scanner")

    from io import BytesIO
    from PIL import Image
    from core.receipt_ai import (
        get_client,
        extract_bill_details,
        pdf_to_images
    )

    api_key = None

    try:
        api_key = st.secrets["OPENAI_API_KEY"]
    except Exception:
        api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        st.error("OPENAI_API_KEY not found. Add it in Streamlit Secrets.")
        st.stop()

    client = get_client(api_key)

    uploaded_files = st.file_uploader(
        "Upload bill images or PDFs",
        type=["png", "jpg", "jpeg", "pdf"],
        accept_multiple_files=True
    )

    if uploaded_files:
        if st.button("Analyze Bills", type="primary"):
            with st.spinner("AI is reading your bills..."):
                for file in uploaded_files:
                    file_name = file.name.lower()

                    if file_name.endswith(".pdf"):
                        images = pdf_to_images(file)
                    else:
                        images = [Image.open(file).convert("RGB")]

                    for image in images:
                        try:
                            extracted = extract_bill_details(client, image)
                        except Exception as e:
                            st.error(f"Could not extract {file.name}: {e}")
                            continue

                        st.session_state.bill_entries.append({
                            "date": extracted.get("date", ""),
                            "transaction_type": extracted.get("transaction_type", "expense"),
                            "name": extracted.get("name", ""),
                            "description": extracted.get("description", ""),
                            "category": extracted.get("category", "Uncategorized"),
                            "subtotal": float(extracted.get("subtotal", 0) or 0),
                            "tax": float(extracted.get("tax", 0) or 0),
                            "total": float(extracted.get("total", 0) or 0),
                            "currency": extracted.get("currency", "CAD"),
                            "confidence": extracted.get("confidence", "medium"),
                            "source_file": file.name
                        })

            st.success("Bills analyzed successfully.")

    if st.button("Clear All Entries"):
        st.session_state.bill_entries = []
        st.rerun()

    if not st.session_state.bill_entries:
        st.info("Upload bills to generate Excel entries.")
        st.stop()

    df = pd.DataFrame(st.session_state.bill_entries)

    st.write("### Review Excel Entries")

    category_options = [
        "Meals",
        "Tools",
        "Software",
        "Office Expense",
        "Employee Cost",
        "Contractor Payment",
        "Rent",
        "Utilities",
        "Internet/Phone",
        "Vehicle",
        "Marketing",
        "Professional Fees",
        "Insurance",
        "Bank Fees",
        "Travel",
        "Income",
        "Uncategorized"
    ]

    edited_df = st.data_editor(
        df,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "transaction_type": st.column_config.SelectboxColumn(
                "Type",
                options=["expense", "income"]
            ),
            "category": st.column_config.SelectboxColumn(
                "Category",
                options=category_options
            ),
            "subtotal": st.column_config.NumberColumn("Subtotal", format="%.2f"),
            "tax": st.column_config.NumberColumn("Tax", format="%.2f"),
            "total": st.column_config.NumberColumn("Total", format="%.2f"),
        }
    )

    if st.button("Save Edited Table"):
        st.session_state.bill_entries = edited_df.to_dict(orient="records")
        st.success("Saved.")

    final_df = pd.DataFrame(st.session_state.bill_entries)

    expense_df = final_df[
        final_df["transaction_type"].astype(str).str.lower() == "expense"
    ].copy()

    income_df = final_df[
        final_df["transaction_type"].astype(str).str.lower() == "income"
    ].copy()

    total_expense = expense_df["total"].sum() if not expense_df.empty else 0
    total_income = income_df["total"].sum() if not income_df.empty else 0

    st.write("### Totals")

    c1, c2 = st.columns(2)
    c1.metric("Total Expenses", f"${total_expense:,.2f}")
    c2.metric("Total Income", f"${total_income:,.2f}")

    left, right = st.columns(2)

    with left:
        st.write("### Expenses")
        st.dataframe(expense_df, use_container_width=True)

    with right:
        st.write("### Income")
        st.dataframe(income_df, use_container_width=True)

    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        final_df.to_excel(writer, index=False, sheet_name="All Entries")

        max_len = max(len(expense_df), len(income_df))

        expense_export = expense_df.reset_index(drop=True).reindex(range(max_len))
        income_export = income_df.reset_index(drop=True).reindex(range(max_len))

        excel_view = pd.DataFrame({
            "Expense Date": expense_export.get("date"),
            "Expense Name": expense_export.get("name"),
            "Expense Description": expense_export.get("description"),
            "Expense Category": expense_export.get("category"),
            "Expense Subtotal": expense_export.get("subtotal"),
            "Expense Tax": expense_export.get("tax"),
            "Expense Total": expense_export.get("total"),

            "Income Date": income_export.get("date"),
            "Income Name": income_export.get("name"),
            "Income Description": income_export.get("description"),
            "Income Category": income_export.get("category"),
            "Income Subtotal": income_export.get("subtotal"),
            "Income Tax": income_export.get("tax"),
            "Income Total": income_export.get("total"),
        })

        excel_view.to_excel(writer, index=False, sheet_name="Income Expense View")

        totals_df = pd.DataFrame([
            {"Metric": "Total Income", "Amount": total_income},
            {"Metric": "Total Expense", "Amount": total_expense},
            {"Metric": "Net Income", "Amount": total_income - total_expense},
        ])
        totals_df.to_excel(writer, index=False, sheet_name="Totals")

    output.seek(0)

    st.download_button(
        "Download Excel",
        data=output,
        file_name="finwise_bill_entries.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
