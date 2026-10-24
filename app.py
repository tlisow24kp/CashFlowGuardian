import sqlite3
from pathlib import Path
from datetime import date, timedelta

import pandas as pd
import streamlit as st


# ==========================================
# PAGE CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="CashFlow Guardian",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ==========================================
# PROFESSIONAL DESIGN
# ==========================================

st.markdown("""
<style>
    .stApp {
        background-color: #F4F7FB;
    }

    [data-testid="stSidebar"] {
        background-color: #102A43;
    }

    [data-testid="stSidebar"] * {
        color: white !important;
    }

    .main-title {
        font-size: 38px;
        font-weight: 800;
        color: #102A43;
        margin-bottom: 0;
    }

    .subtitle {
        font-size: 16px;
        color: #627D98;
        margin-bottom: 25px;
    }

    .section-title {
        color: #102A43;
        font-size: 23px;
        font-weight: 700;
    }

    div[data-testid="stMetric"] {
        background-color: white;
        border: 1px solid #E1E8F0;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 3px 10px rgba(16, 42, 67, 0.05);
    }

    div[data-testid="stMetricLabel"] {
        color: #627D98;
        font-weight: 600;
    }

    div[data-testid="stMetricValue"] {
        color: #102A43;
    }

    div.stButton > button,
    div.stFormSubmitButton > button {
        background-color: #087F5B;
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        padding: 9px 18px;
    }

    .footer {
        text-align: center;
        color: #829AB1;
        font-size: 13px;
        padding: 25px 0 10px 0;
    }
</style>
""", unsafe_allow_html=True)


# ==========================================
# DATABASE
# ==========================================

DATABASE = Path(__file__).resolve().parent / "cashflow.db"


def get_connection():
    return sqlite3.connect(DATABASE)


def create_table():
    with get_connection() as conn:
        # Create the transactions table if it does not exist
        conn.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                transaction_type TEXT NOT NULL,
                amount REAL NOT NULL,
                transaction_date TEXT NOT NULL,
                user_id INTEGER
            )
        """)

        # Check whether user_id already exists
        columns = conn.execute(
            "PRAGMA table_info(transactions)"
        ).fetchall()

        column_names = [column[1] for column in columns]

        # Add user_id to an existing database if necessary
        if "user_id" not in column_names:
            conn.execute("""
                ALTER TABLE transactions
                ADD COLUMN user_id INTEGER
            """)

def add_transaction(description, transaction_type, amount, transaction_date):
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO transactions
            (description, transaction_type, amount, transaction_date)
            VALUES (?, ?, ?, ?)
        """, (
            description,
            transaction_type,
            amount,
            transaction_date.isoformat()
        ))


def update_transaction(
    transaction_id,
    description,
    transaction_type,
    amount,
    transaction_date
):
    with get_connection() as conn:
        conn.execute("""
            UPDATE transactions
            SET description = ?,
                transaction_type = ?,
                amount = ?,
                transaction_date = ?
            WHERE id = ?
        """, (
            description,
            transaction_type,
            amount,
            transaction_date.isoformat(),
            transaction_id
        ))


def delete_transaction(transaction_id):
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM transactions WHERE id = ?",
            (transaction_id,)
        )


def get_transactions():
    with get_connection() as conn:
        return pd.read_sql_query("""
            SELECT id, description, transaction_type, amount, transaction_date
            FROM transactions
            ORDER BY transaction_date, id
        """, conn)


create_table()


# ==========================================
# SIDEBAR
# ==========================================

st.sidebar.markdown("# 💰 CashFlow")
st.sidebar.markdown("### GUARDIAN")
st.sidebar.markdown("---")
st.sidebar.write("### ⚙️ Business Settings")

business_name = st.sidebar.text_input(
    "Business name",
    value="My Business"
)

starting_cash = st.sidebar.number_input(
    "Cash available today (R)",
    min_value=0.0,
    value=18500.0,
    step=500.0
)

warning_limit = st.sidebar.number_input(
    "Low-cash warning limit (R)",
    min_value=0.0,
    value=5000.0,
    step=500.0
)

forecast_days = st.sidebar.selectbox(
    "Forecast period",
    [7, 14, 30, 60, 90],
    index=2,
    format_func=lambda x: f"{x} days"
)

st.sidebar.markdown("---")
st.sidebar.caption("Plan smarter. Protect your cash.")


# ==========================================
# HEADER
# ==========================================

st.markdown(
    '<p class="main-title">💰 CashFlow Guardian</p>',
    unsafe_allow_html=True
)

st.markdown(
    f'<p class="subtitle">{business_name} | Financial Overview | '
    f'{date.today().strftime("%d %B %Y")}</p>',
    unsafe_allow_html=True
)

st.info(
    "Monitor your money, track expected transactions, "
    "and identify potential cash shortages."
)


# ==========================================
# ADD TRANSACTION
# ==========================================

with st.expander("➕ Add a New Income or Expense"):

    with st.form("add_transaction_form", clear_on_submit=True):

        description = st.text_input(
            "Transaction description",
            placeholder="e.g. Customer payment or Rent"
        )

        col1, col2 = st.columns(2)

        with col1:
            transaction_type = st.selectbox(
                "Transaction type",
                ["Income", "Expense"],
                key="add_type"
            )

        with col2:
            amount = st.number_input(
                "Amount (R)",
                min_value=0.01,
                value=100.0,
                step=50.0,
                key="add_amount"
            )

        transaction_date = st.date_input(
            "Expected transaction date",
            value=date.today(),
            min_value=date.today(),
            key="add_date"
        )

        submitted = st.form_submit_button(
            "💾 Save Transaction",
            use_container_width=True
        )

        if submitted:
            if not description.strip():
                st.error("Please enter a description.")
            else:
                add_transaction(
                    description.strip(),
                    transaction_type,
                    amount,
                    transaction_date
                )
                st.success("Transaction saved!")
                st.rerun()


# ==========================================
# LOAD TRANSACTIONS
# ==========================================

transactions = get_transactions()

today = date.today()
end_date = today + timedelta(days=int(forecast_days))

if not transactions.empty:

    transactions["transaction_date"] = pd.to_datetime(
        transactions["transaction_date"]
    ).dt.date

    total_income = transactions.loc[
        transactions["transaction_type"] == "Income", "amount"
    ].sum()

    total_expenses = transactions.loc[
        transactions["transaction_type"] == "Expense", "amount"
    ].sum()

else:
    total_income = 0.0
    total_expenses = 0.0

projected_cash = starting_cash + total_income - total_expenses


# ==========================================
# FINANCIAL SUMMARY
# ==========================================

st.markdown(
    '<p class="section-title">📊 Financial Summary</p>',
    unsafe_allow_html=True
)

col1, col2 = st.columns(2)

with col1:
    st.metric("💵 Starting Cash", f"R {starting_cash:,.2f}")

with col2:
    st.metric("📈 Recorded Income", f"R {total_income:,.2f}")

col3, col4 = st.columns(2)

with col3:
    st.metric("📉 Recorded Expenses", f"R {total_expenses:,.2f}")

with col4:
    st.metric(
        "💰 Projected Cash",
        f"R {projected_cash:,.2f}",
        delta=f"R {projected_cash - starting_cash:,.2f}"
    )


# ==========================================
# CASH-FLOW FORECAST
# ==========================================

st.markdown("---")
st.markdown(
    '<p class="section-title">📅 Day-by-Day Cash Forecast</p>',
    unsafe_allow_html=True
)

st.caption(
    "Forecasts assume all recorded transactions happen as planned."
)

daily_transactions = {}

if not transactions.empty:

    for _, transaction in transactions.iterrows():

        transaction_day = transaction["transaction_date"]

        if today <= transaction_day <= end_date:

            change = float(transaction["amount"])

            if transaction["transaction_type"] == "Expense":
                change = -change

            daily_transactions[transaction_day] = (
                daily_transactions.get(transaction_day, 0.0) + change
            )

forecast = []
running_balance = starting_cash

for day_number in range(int(forecast_days) + 1):

    forecast_date = today + timedelta(days=day_number)
    daily_change = daily_transactions.get(forecast_date, 0.0)
    running_balance += daily_change

    if running_balance < 0:
        status = "🚨 Negative balance"
    elif running_balance < warning_limit:
        status = "⚠️ Low cash"
    else:
        status = "✅ Healthy"

    forecast.append({
        "Date": forecast_date,
        "Money In/Out (R)": round(daily_change, 2),
        "Projected Balance (R)": round(running_balance, 2),
        "Status": status
    })

forecast_df = pd.DataFrame(forecast)


# ==========================================
# CASH-FLOW CHART
# ==========================================

st.markdown(
    '<p class="section-title">📈 Cash-Flow Trend</p>',
    unsafe_allow_html=True
)

chart_data = forecast_df.set_index("Date")

st.line_chart(
    chart_data[["Projected Balance (R)"]],
    x_label="Date",
    y_label="Projected Cash (R)"
)


# ==========================================
# CASH WARNINGS
# ==========================================

low_cash_days = forecast_df[
    forecast_df["Projected Balance (R)"] < warning_limit
]

if not low_cash_days.empty:

    first_low_day = low_cash_days.iloc[0]

    st.error(
        f"⚠️ CASH-FLOW ALERT: Your projected balance first falls below "
        f"R {warning_limit:,.2f} on "
        f"{first_low_day['Date'].strftime('%d %B %Y')}. "
        f"Projected balance: "
        f"R {first_low_day['Projected Balance (R)']:,.2f}."
    )

else:
    st.success(
        "✅ Your projected balance stays at or above your warning limit "
        "during the selected forecast period."
    )


# ==========================================
# DAILY FORECAST TABLE
# ==========================================

with st.expander("View Daily Forecast Details"):

    display_forecast = forecast_df.copy()

    display_forecast["Date"] = display_forecast["Date"].apply(
        lambda x: x.strftime("%d %b %Y")
    )

    st.dataframe(
        display_forecast,
        use_container_width=True,
        hide_index=True
    )


# ==========================================
# TRANSACTION HISTORY
# ==========================================

st.markdown("---")
st.markdown(
    '<p class="section-title">📋 Transaction History</p>',
    unsafe_allow_html=True
)

if not transactions.empty:

    display_transactions = transactions.copy()

    display_transactions["transaction_date"] = (
        display_transactions["transaction_date"].astype(str)
    )

    display_transactions = display_transactions.rename(columns={
        "id": "ID",
        "description": "Description",
        "transaction_type": "Type",
        "amount": "Amount (R)",
        "transaction_date": "Date"
    })

    display_transactions["Amount (R)"] = (
        display_transactions["Amount (R)"].map(
            lambda amount: f"R {amount:,.2f}"
        )
    )

    st.dataframe(
        display_transactions,
        use_container_width=True,
        hide_index=True
    )

    csv_data = display_transactions.to_csv(index=False).encode("utf-8")

    st.download_button(
        "📥 Download Transaction History",
        data=csv_data,
        file_name="cashflow_transactions.csv",
        mime="text/csv"
    )

else:
    st.info("No transactions recorded yet.")


# ==========================================
# EDIT AND DELETE TRANSACTIONS
# ==========================================

st.markdown("---")

st.markdown(
    '<p class="section-title">✏️ Manage Transactions</p>',
    unsafe_allow_html=True
)

if not transactions.empty:

    transaction_options = {}

    for _, transaction in transactions.iterrows():

        label = (
            f"ID {transaction['id']} | "
            f"{transaction['description']} | "
            f"{transaction['transaction_type']} | "
            f"R {transaction['amount']:,.2f} | "
            f"{transaction['transaction_date']}"
        )

        transaction_options[label] = int(transaction["id"])

    selected_label = st.selectbox(
        "Select a transaction to manage",
        list(transaction_options.keys())
    )

    selected_id = transaction_options[selected_label]

    selected_transaction = transactions[
        transactions["id"] == selected_id
    ].iloc[0]

    edit_tab, delete_tab = st.tabs([
        "✏️ Edit Transaction",
        "🗑️ Delete Transaction"
    ])

    # EDIT TRANSACTION
    with edit_tab:

        with st.form("edit_transaction_form"):

            edit_description = st.text_input(
                "Description",
                value=str(selected_transaction["description"])
            )

            current_type = str(selected_transaction["transaction_type"])

            edit_type = st.selectbox(
                "Transaction type",
                ["Income", "Expense"],
                index=0 if current_type == "Income" else 1
            )

            edit_amount = st.number_input(
                "Amount (R)",
                min_value=0.01,
                value=float(selected_transaction["amount"]),
                step=50.0
            )

            edit_date = st.date_input(
                "Transaction date",
                value=selected_transaction["transaction_date"],
                min_value=date.today()
            )

            save_edit = st.form_submit_button(
                "💾 Save Changes",
                use_container_width=True
            )

            if save_edit:

                if not edit_description.strip():
                    st.error("Description cannot be empty.")

                elif edit_amount <= 0:
                    st.error("Amount must be greater than zero.")

                else:
                    update_transaction(
                        selected_id,
                        edit_description.strip(),
                        edit_type,
                        edit_amount,
                        edit_date
                    )

                    st.success("Transaction updated successfully!")
                    st.rerun()

    # DELETE TRANSACTION
    with delete_tab:

        st.warning(
            "Deleting a transaction is permanent. "
            "The transaction will be removed from your database."
        )

        confirm_delete = st.checkbox(
            "I confirm that I want to delete this transaction.",
            key=f"confirm_delete_{selected_id}"
        )

        if st.button(
            "🗑️ Delete Selected Transaction",
            disabled=not confirm_delete,
            use_container_width=True
        ):

            delete_transaction(selected_id)

            st.success("Transaction deleted successfully!")
            st.rerun()

else:

    st.info(
        "Add a transaction first. It will appear here when you are ready "
        "to edit or delete it."
    )


# ==========================================
# FOOTER
# ==========================================

st.markdown("---")

st.markdown(
    '<div class="footer">'
    'CashFlow Guardian © 2026 | Plan smarter. Protect your cash.<br>'
    'Forecasts are estimates based on the transactions entered.'
    '</div>',
    unsafe_allow_html=True
)