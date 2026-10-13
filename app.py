
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


# --------------------------------------------------
# 1. PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Personal Expense Tracker",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)


# --------------------------------------------------
# 2. CUSTOM DESIGN AND CSS
# --------------------------------------------------

st.markdown(
    """
    <style>
    .stApp {
        background-color: #F4F7FB;
    }

    /* Light sidebar for readable dates and text */
    [data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 1px solid #E2E8F0;
    }

    [data-testid="stSidebar"] * {
        color: #17243A;
    }

    /* Date input fields */
    [data-testid="stDateInput"] input {
        background-color: #FFFFFF !important;
        color: #17243A !important;
        -webkit-text-fill-color: #17243A !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 8px !important;
        caret-color: #17243A !important;
    }

    [data-testid="stDateInput"] label {
        color: #17243A !important;
        font-weight: 600;
    }

    /* Calendar popup */
    [data-baseweb="calendar"] {
        background-color: #FFFFFF !important;
        color: #17243A !important;
    }

    /* Dashboard header */
    .hero {
        background: linear-gradient(120deg, #17243A, #087F8C);
        padding: 30px;
        border-radius: 18px;
        color: white;
        margin-bottom: 25px;
    }

    .hero h1 {
        color: white;
        margin-bottom: 8px;
        font-size: 34px;
    }

    .hero p {
        color: #E0F2F1;
        margin-bottom: 0;
        font-size: 16px;
    }

    /* Metric cards */
    [data-testid="stMetric"] {
        background-color: white;
        padding: 18px;
        border-radius: 14px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 3px 10px rgba(23, 36, 58, 0.04);
    }

    h2, h3 {
        color: #17243A;
    }

    /* Buttons */
    .stButton button,
    .stFormSubmitButton button {
        border-radius: 8px;
        font-weight: 600;
    }

    /* Dataframe container */
    [data-testid="stDataFrame"] {
        border-radius: 12px;
        overflow: hidden;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------
# 3. LOAD DATASET
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "personal_expense_dataset.csv"


@st.cache_data
def load_data(file_path):
    if not file_path.exists():
        return None

    df = pd.read_csv(file_path)

    required_columns = [
        "Date",
        "Category",
        "Amount",
        "Payment_Mode",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            "Missing columns in CSV: "
            + ", ".join(missing_columns)
        )

    df["Date"] = pd.to_datetime(
        df["Date"],
        errors="coerce",
    )

    df["Amount"] = pd.to_numeric(
        df["Amount"],
        errors="coerce",
    )

    df["Category"] = df["Category"].fillna("Other").astype(str)
    df["Payment_Mode"] = (
        df["Payment_Mode"].fillna("Other").astype(str)
    )

    df = df.dropna(subset=["Date", "Amount"])
    df = df[df["Amount"] >= 0].copy()

    # Always derive Month from Date for consistent analysis.
    df["Month"] = df["Date"].dt.strftime("%Y-%m")

    return df


try:
    df = load_data(DATA_FILE)
except Exception as error:
    st.error(f"Could not load the dataset: {error}")
    st.stop()

if df is None:
    st.error(
        "Dataset not found. Please place "
        "'personal_expense_dataset.csv' in the same folder as app.py."
    )
    st.stop()

if df.empty:
    st.warning("Your dataset has no valid expense records.")
    st.stop()


# --------------------------------------------------
# 4. HEADER
# --------------------------------------------------

st.markdown(
    """
    <div class="hero">
        <h1>💰 Personal Expense Tracker</h1>
        <p>
            Track your spending, understand your habits,
            and manage your monthly budget.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------
# 5. SIDEBAR FILTERS
# --------------------------------------------------

st.sidebar.title("⚙️ Dashboard Controls")
st.sidebar.markdown("Filter and manage your expenses below.")

st.sidebar.divider()
st.sidebar.subheader("📅 Date Range")

min_date = df["Date"].min().date()
max_date = df["Date"].max().date()

# Separate date fields make the selected dates easier to read.
start_date = st.sidebar.date_input(
    "Start date",
    value=min_date,
    min_value=min_date,
    max_value=max_date,
    format="DD/MM/YYYY",
    key="start_date",
)

end_date = st.sidebar.date_input(
    "End date",
    value=max_date,
    min_value=min_date,
    max_value=max_date,
    format="DD/MM/YYYY",
    key="end_date",
)

st.sidebar.divider()
st.sidebar.subheader("🏷️ Category")

all_categories = sorted(df["Category"].unique().tolist())

selected_categories = st.sidebar.multiselect(
    "Choose categories",
    options=all_categories,
    default=all_categories,
)

st.sidebar.divider()
st.sidebar.subheader("💳 Payment Method")

all_payment_modes = sorted(
    df["Payment_Mode"].unique().tolist()
)

selected_payment_modes = st.sidebar.multiselect(
    "Choose payment methods",
    options=all_payment_modes,
    default=all_payment_modes,
)

st.sidebar.divider()
st.sidebar.subheader("🎯 Monthly Budget")

monthly_budget = st.sidebar.number_input(
    "Enter your monthly budget (₹)",
    min_value=0.0,
    value=10000.0,
    step=500.0,
    format="%.2f",
)

st.sidebar.caption(
    "The budget is compared with expenses for the selected month."
)


# --------------------------------------------------
# 6. FILTER DATA
# --------------------------------------------------

filtered = df.copy()

if start_date > end_date:
    st.sidebar.error("Start date must be on or before end date.")
    filtered = filtered.iloc[0:0].copy()
else:
    filtered = filtered[
        (filtered["Date"].dt.date >= start_date)
        & (filtered["Date"].dt.date <= end_date)
    ].copy()

if selected_categories:
    filtered = filtered[
        filtered["Category"].isin(selected_categories)
    ].copy()
else:
    filtered = filtered.iloc[0:0].copy()

if selected_payment_modes:
    filtered = filtered[
        filtered["Payment_Mode"].isin(selected_payment_modes)
    ].copy()
else:
    filtered = filtered.iloc[0:0].copy()


# --------------------------------------------------
# 7. SUMMARY METRICS
# --------------------------------------------------

st.subheader("📊 Expense Overview")

total_expense = filtered["Amount"].sum()
average_expense = filtered["Amount"].mean() if not filtered.empty else 0
transaction_count = len(filtered)
largest_expense = filtered["Amount"].max() if not filtered.empty else 0

metric1, metric2, metric3, metric4 = st.columns(4)

metric1.metric(
    "Total Expenses",
    f"₹{total_expense:,.2f}",
)

metric2.metric(
    "Average Transaction",
    f"₹{average_expense:,.2f}",
)

metric3.metric(
    "Number of Transactions",
    f"{transaction_count:,}",
)

metric4.metric(
    "Largest Expense",
    f"₹{largest_expense:,.2f}",
)


# --------------------------------------------------
# 8. CHARTS
# --------------------------------------------------

st.divider()
st.subheader("📈 Spending Analysis")

if filtered.empty:
    st.info(
        "No expenses match the selected filters. "
        "Try choosing another date range or category."
    )
else:
    chart_col1, chart_col2 = st.columns(2)

    # Category chart
    with chart_col1:
        category_summary = (
            filtered.groupby("Category", as_index=False)["Amount"]
            .sum()
            .sort_values("Amount", ascending=False)
        )

        category_fig = px.pie(
            category_summary,
            names="Category",
            values="Amount",
            hole=0.48,
            title="Expenses by Category",
            color_discrete_sequence=px.colors.qualitative.Set2,
        )

        category_fig.update_layout(
            paper_bgcolor="white",
            plot_bgcolor="white",
            font_color="#17243A",
            legend_title_text="Category",
            margin=dict(t=60, b=20, l=20, r=20),
        )

        st.plotly_chart(
            category_fig,
            use_container_width=True,
        )

    # Monthly chart
    with chart_col2:
        monthly_summary = (
            filtered.assign(
                Month=filtered["Date"].dt.to_period("M").astype(str)
            )
            .groupby("Month", as_index=False)["Amount"]
            .sum()
            .sort_values("Month")
        )

        monthly_fig = px.bar(
            monthly_summary,
            x="Month",
            y="Amount",
            title="Monthly Spending",
            labels={
                "Month": "Month",
                "Amount": "Total Expense (₹)",
            },
            color="Amount",
            color_continuous_scale=["#9AD9D2", "#087F8C"],
        )

        monthly_fig.update_layout(
            paper_bgcolor="white",
            plot_bgcolor="white",
            font_color="#17243A",
            coloraxis_showscale=False,
            xaxis_title="Month",
            yaxis_title="Amount (₹)",
            margin=dict(t=60, b=20, l=20, r=20),
        )

        st.plotly_chart(
            monthly_fig,
            use_container_width=True,
        )

    # Payment method chart
    payment_summary = (
        filtered.groupby("Payment_Mode", as_index=False)["Amount"]
        .sum()
        .sort_values("Amount", ascending=False)
    )

    payment_fig = px.bar(
        payment_summary,
        x="Payment_Mode",
        y="Amount",
        title="Spending by Payment Method",
        labels={
            "Payment_Mode": "Payment Method",
            "Amount": "Total Expense (₹)",
        },
        color="Payment_Mode",
        color_discrete_sequence=px.colors.qualitative.Pastel,
    )

    payment_fig.update_layout(
        paper_bgcolor="white",
        plot_bgcolor="white",
        font_color="#17243A",
        showlegend=False,
        xaxis_title="Payment Method",
        yaxis_title="Amount (₹)",
        margin=dict(t=60, b=20, l=20, r=20),
    )

    st.plotly_chart(
        payment_fig,
        use_container_width=True,
    )


# --------------------------------------------------
# 9. INSIGHTS AND BUDGET
# --------------------------------------------------

st.divider()
st.subheader("💡 Spending Insights")

if not filtered.empty:
    insight_col1, insight_col2 = st.columns(2)

    with insight_col1:
        category_totals = filtered.groupby("Category")["Amount"].sum()

        highest_category = category_totals.idxmax()
        highest_category_amount = category_totals.max()

        st.markdown("#### Highest Spending Category")
        st.write(f"**{highest_category}**")
        st.write(f"Total: ₹{highest_category_amount:,.2f}")

        if total_expense > 0:
            percentage = (
                highest_category_amount / total_expense
            ) * 100

            st.write(
                f"This category accounts for "
                f"{percentage:.1f}% of your filtered expenses."
            )

    with insight_col2:
        st.markdown("#### Budget Status")

        # Use the latest month present in the filtered data.
        selected_month = filtered["Date"].dt.to_period("M").max()

        month_expenses = df[
            df["Date"].dt.to_period("M") == selected_month
        ]["Amount"].sum()

        st.write(f"**Month:** {selected_month.strftime('%B %Y')}")
        st.write(f"**Expenses for this month:** ₹{month_expenses:,.2f}")

        if monthly_budget > 0:
            budget_used = month_expenses / monthly_budget
            progress = min(budget_used, 1.0)

            st.progress(progress)

            st.write(
                f"Budget used: {budget_used * 100:.1f}%"
            )

            if month_expenses > monthly_budget:
                st.error(
                    f"You are ₹{month_expenses - monthly_budget:,.2f} "
                    "over your monthly budget."
                )
            else:
                st.success(
                    f"You have ₹{monthly_budget - month_expenses:,.2f} "
                    "remaining in your monthly budget."
                )
        else:
            st.info("Enter a budget greater than ₹0 to track your budget.")

else:
    st.info("Insights will appear when matching expense records are available.")


# --------------------------------------------------
# 10. TRANSACTION TABLE AND SEARCH
# --------------------------------------------------

st.divider()
st.subheader("🧾 Transaction History")

search_text = st.text_input(
    "🔍 Search transactions by category or payment method",
    placeholder="For example: Food, Shopping, UPI...",
)

transactions = filtered.copy()

if search_text.strip():
    search_value = search_text.strip().lower()

    matches = (
        transactions["Category"].str.lower().str.contains(
            search_value, na=False
        )
        | transactions["Payment_Mode"].str.lower().str.contains(
            search_value, na=False
        )
    )

    transactions = transactions[matches].copy()

if not transactions.empty:
    display_transactions = transactions.copy()
    display_transactions["Date"] = (
        display_transactions["Date"].dt.strftime("%d/%m/%Y")
    )

    display_transactions = display_transactions[
        ["Date", "Category", "Amount", "Payment_Mode", "Month"]
    ]

    st.dataframe(
        display_transactions.sort_values(
            "Date",
            ascending=False,
        ),
        use_container_width=True,
        hide_index=True,
    )

    csv_data = transactions.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="⬇️ Download Filtered Transactions (CSV)",
        data=csv_data,
        file_name="filtered_expenses.csv",
        mime="text/csv",
    )
else:
    st.info("No transactions match your search and filters.")


# --------------------------------------------------
# 11. ADD A NEW EXPENSE
# --------------------------------------------------

st.divider()
st.subheader("➕ Add a New Expense")

with st.form("add_expense_form", clear_on_submit=True):
    form_col1, form_col2 = st.columns(2)

    with form_col1:
        new_date = st.date_input(
            "Expense date",
            value=pd.Timestamp.today().date(),
            format="DD/MM/YYYY",
        )

        new_category = st.selectbox(
            "Category",
            options=all_categories,
        )

        new_amount = st.number_input(
            "Amount (₹)",
            min_value=0.01,
            value=100.0,
            step=10.0,
        )

    with form_col2:
        new_payment_mode = st.selectbox(
            "Payment method",
            options=all_payment_modes,
        )

        st.caption(
            "The new expense will be saved to your original CSV dataset."
        )

    submitted = st.form_submit_button(
        "Save Expense",
        use_container_width=True,
    )

    if submitted:
        new_row = pd.DataFrame(
            [
                {
                    "Date": pd.Timestamp(new_date),
                    "Category": new_category,
                    "Amount": new_amount,
                    "Payment_Mode": new_payment_mode,
                    "Month": pd.Timestamp(new_date).strftime("%Y-%m"),
                }
            ]
        )

        try:
            # Preserve any extra columns already in the original CSV.
            for column in df.columns:
                if column not in new_row.columns:
                    new_row[column] = pd.NA

            new_row = new_row[df.columns]

            existing_data = pd.read_csv(DATA_FILE)
            updated_data = pd.concat(
                [existing_data, new_row],
                ignore_index=True,
            )

            updated_data.to_csv(DATA_FILE, index=False)

            st.cache_data.clear()

            st.success("Expense saved successfully!")
            st.rerun()

        except Exception as error:
            st.error(f"Could not save the expense: {error}")


# --------------------------------------------------
# 12. FOOTER
# --------------------------------------------------

st.divider()

st.markdown(
    """
    <div style="text-align:center; color:#64748B; padding:10px;">
        Personal Expense Tracker · Built with Python, Streamlit,
        Pandas and Plotly
    </div>
    """,
    unsafe_allow_html=True,
)
