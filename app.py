import sqlite3
import html
from pathlib import Path
from datetime import date, timedelta

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from auth import show_auth_page, logout_button


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="CashFlow Guardian",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# DATABASE CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "cashflow.db"


def get_connection():
    """Create a connection to the SQLite database."""

    connection = sqlite3.connect(
        str(DB_PATH),
        check_same_thread=False
    )

    connection.row_factory = sqlite3.Row

    return connection


def initialise_database():
    """Create the transactions table if it does not exist."""

    connection = get_connection()

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT NOT NULL,
            transaction_type TEXT NOT NULL,
            amount REAL NOT NULL,
            transaction_date TEXT NOT NULL,
            user_id INTEGER
        )
        """
    )

    columns = connection.execute(
        "PRAGMA table_info(transactions)"
    ).fetchall()

    column_names = [column["name"] for column in columns]

    if "user_id" not in column_names:
        connection.execute(
            "ALTER TABLE transactions ADD COLUMN user_id INTEGER"
        )

    connection.commit()
    connection.close()


initialise_database()


# ============================================================
# AUTHENTICATION
# ============================================================

if "user" not in st.session_state:
    show_auth_page()
    st.stop()


current_user = st.session_state["user"]

if not isinstance(current_user, dict):
    st.error(
        "The logged-in user information is not in the expected format. "
        "Please check auth.py."
    )
    st.stop()


current_user_id = current_user.get(
    "id",
    current_user.get("user_id")
)

current_username = current_user.get(
    "username",
    "User"
)

saved_business_name = current_user.get(
    "business_name",
    "My Business"
)

if current_user_id is None:
    st.error(
        "Your account does not have a user ID. "
        "Please check how auth.py stores the logged-in user."
    )
    st.stop()


# ============================================================
# CUSTOM CSS AND ANIMATIONS
# ============================================================

st.markdown(
    """
    <style>

    /* ==========================================
       GENERAL APPLICATION DESIGN
       ========================================== */

    .stApp {
        background-color: #F4F7FB;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1500px;
        animation: dashboardEnter 0.8s ease-out both;
    }

    @keyframes dashboardEnter {
        from {
            opacity: 0;
            transform: translateY(14px);
        }

        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    /* ==========================================
       SIDEBAR
       ========================================== */

    section[data-testid="stSidebar"] {
        background-color: #102A43;
    }

    section[data-testid="stSidebar"] * {
        color: #FFFFFF;
    }

    section[data-testid="stSidebar"] .stButton button {
        background-color: #087F5B;
        color: #FFFFFF;
        border: none;
        border-radius: 8px;
        font-weight: 600;
    }

    section[data-testid="stSidebar"] .stButton button:hover {
        background-color: #099268;
    }

    /* ==========================================
       HEADINGS
       ========================================== */

    h1, h2, h3 {
        color: #102A43;
        font-weight: 700;
    }

    .section-title {
        color: #102A43;
        font-size: 1.35rem;
        font-weight: 700;
        margin-top: 1rem;
        margin-bottom: 0.8rem;
    }

    /* ==========================================
       ANIMATED WELCOME BANNER
       ========================================== */

    .welcome-banner {
        position: relative;
        overflow: hidden;
        padding: 28px 32px;
        margin: 10px 0 25px 0;
        border-radius: 18px;

        background: linear-gradient(
            120deg,
            #102A43,
            #087F5B,
            #102A43
        );

        background-size: 200% 200%;

        color: #FFFFFF;

        box-shadow: 0 8px 24px rgba(16, 42, 67, 0.15);

        animation:
            bannerEnter 0.9s ease-out,
            bannerGlow 8s ease infinite;
    }

    .welcome-banner h2 {
        color: #FFFFFF !important;
        font-size: 1.8rem;
        margin: 0 0 8px 0;
    }

    .welcome-banner p {
        color: #E6F4F1;
        font-size: 1rem;
        margin: 0;
    }

    .welcome-banner .banner-icon {
        font-size: 2.8rem;
        margin-bottom: 8px;
    }

    @keyframes bannerEnter {
        from {
            opacity: 0;
            transform: translateY(20px);
        }

        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    @keyframes bannerGlow {
        0% {
            background-position: 0% 50%;
        }

        50% {
            background-position: 100% 50%;
        }

        100% {
            background-position: 0% 50%;
        }
    }

    /* ==========================================
       METRIC CARDS
       ========================================== */

    div[data-testid="stMetric"] {
        background-color: #FFFFFF;
        border: 1px solid #D9E2EC;
        border-left: 5px solid #087F5B;
        border-radius: 12px;
        padding: 20px;

        box-shadow: 0 4px 12px rgba(16, 42, 67, 0.06);

        animation: fadeIn 0.8s ease-in;

        transition:
            transform 0.3s ease,
            box-shadow 0.3s ease,
            border-color 0.3s ease;
    }

    @media (hover: hover) {
        div[data-testid="stMetric"]:hover {
            transform: translateY(-6px) scale(1.01);

            box-shadow: 0 12px 26px rgba(16, 42, 67, 0.13);

            border-left-color: #D4AF37;
        }
    }

    div[data-testid="stMetricLabel"] {
        color: #627D98;
        font-weight: 600;
    }

    div[data-testid="stMetricValue"] {
        color: #102A43;
        font-weight: 800;
    }

    /* ==========================================
       ANIMATED CASH COUNTER
       ========================================== */

    .cash-counter-card {
        background: linear-gradient(
            135deg,
            #FFFFFF,
            #E6F4F1
        );

        border: 1px solid #C6E8DB;
        border-radius: 16px;

        padding: 24px;
        margin: 12px 0 22px 0;

        box-shadow: 0 6px 18px rgba(16, 42, 67, 0.07);

        animation: fadeIn 0.9s ease-out;
    }

    .cash-counter-label {
        color: #486581;
        font-size: 0.95rem;
        font-weight: 600;
        margin-bottom: 8px;
    }

    .cash-counter-value {
        color: #087F5B;
        font-size: 2.4rem;
        font-weight: 800;
        line-height: 1.3;
        overflow-wrap: anywhere;
    }

    .cash-counter-caption {
        color: #627D98;
        font-size: 0.9rem;
        margin-top: 8px;
    }

    /* ==========================================
       CASH HEALTH INDICATOR
       ========================================== */

    .health-card {
        background-color: #FFFFFF;
        border: 1px solid #D9E2EC;
        border-radius: 16px;
        padding: 22px;
        margin: 15px 0;

        box-shadow: 0 5px 16px rgba(16, 42, 67, 0.06);

        animation: fadeIn 0.8s ease-out;
    }

    .health-heading {
        color: #102A43;
        font-size: 1.15rem;
        font-weight: 700;
        margin-bottom: 8px;
    }

    .health-description {
        color: #627D98;
        font-size: 0.92rem;
        margin-bottom: 14px;
    }

    .health-track {
        width: 100%;
        height: 16px;
        overflow: hidden;
        background-color: #E4EAF0;
        border-radius: 999px;
    }

    .health-fill {
        height: 100%;
        border-radius: 999px;

        animation: healthFill 1.2s ease-out both;

        transition: width 0.5s ease;
    }

    @keyframes healthFill {
        from {
            width: 0%;
        }
    }

    .health-status {
        font-size: 1rem;
        font-weight: 700;
        margin-top: 12px;
    }

    /* ==========================================
       BUTTONS
       ========================================== */

    .stButton button,
    .stDownloadButton button,
    .stFormSubmitButton button {
        background-color: #087F5B;
        color: #FFFFFF;

        border: none;
        border-radius: 8px;

        padding: 0.55rem 1rem;

        font-weight: 600;

        transition:
            background-color 0.2s ease,
            transform 0.2s ease,
            box-shadow 0.2s ease;
    }

    @media (hover: hover) {
        .stButton button:hover,
        .stDownloadButton button:hover,
        .stFormSubmitButton button:hover {
            background-color: #066649;
            color: #FFFFFF;

            transform: translateY(-2px);

            box-shadow: 0 5px 12px rgba(8, 127, 91, 0.2);
        }
    }

    .stButton button:active,
    .stDownloadButton button:active,
    .stFormSubmitButton button:active {
        transform: scale(0.98);
    }

    /* ==========================================
       INPUT FIELDS
       ========================================== */

    div[data-baseweb="input"] input,
    div[data-baseweb="textarea"] textarea {
        border-radius: 8px;

        transition:
            border-color 0.2s ease,
            box-shadow 0.2s ease;
    }

    div[data-baseweb="input"]:focus-within,
    div[data-baseweb="textarea"]:focus-within {
        box-shadow: 0 0 0 2px rgba(8, 127, 91, 0.12);
        border-radius: 8px;
    }

    /* ==========================================
       FORMS
       ========================================== */

    div[data-testid="stForm"] {
        background-color: #FFFFFF;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #D9E2EC;
    }

    /* ==========================================
       ALERTS AND SECTIONS
       ========================================== */

    div[data-testid="stAlert"] {
        border-radius: 10px;
    }

    [data-testid="stVerticalBlockBorderWrapper"] {
        animation: sectionAppear 0.7s ease-out both;
    }

    @keyframes sectionAppear {
        from {
            opacity: 0.65;
        }

        to {
            opacity: 1;
        }
    }

    /* ==========================================
       GOLD DIVIDER
       ========================================== */

    .gold-line {
        border: none;
        height: 3px;

        background: linear-gradient(
            90deg,
            #087F5B,
            #D4AF37,
            #087F5B
        );

        background-size: 200% 100%;

        animation: dividerFlow 5s linear infinite;

        margin-top: 10px;
        margin-bottom: 20px;
    }

    @keyframes dividerFlow {
        from {
            background-position: 0% center;
        }

        to {
            background-position: 200% center;
        }
    }

    /* ==========================================
       FOOTER
       ========================================== */

    .footer {
        text-align: center;
        color: #627D98;
        font-size: 0.9rem;
        padding-top: 25px;
        padding-bottom: 10px;
    }

    /* ==========================================
       ACCESSIBILITY
       ========================================== */

    @media (prefers-reduced-motion: reduce) {
        *,
        *::before,
        *::after {
            animation-duration: 0.01ms !important;
            animation-iteration-count: 1 !important;
            transition-duration: 0.01ms !important;
            scroll-behavior: auto !important;
        }
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# TRANSACTION FUNCTIONS
# ============================================================

def add_transaction(
    description,
    transaction_type,
    amount,
    transaction_date
):
    """Save a transaction for the logged-in user."""

    connection = get_connection()

    try:
        connection.execute(
            """
            INSERT INTO transactions (
                description,
                transaction_type,
                amount,
                transaction_date,
                user_id
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                description.strip(),
                transaction_type,
                float(amount),
                transaction_date.isoformat(),
                current_user_id
            )
        )

        connection.commit()

    finally:
        connection.close()


def get_transactions():
    """Retrieve transactions belonging to the logged-in user."""

    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT
                id,
                description,
                transaction_type,
                amount,
                transaction_date
            FROM transactions
            WHERE user_id = ?
            ORDER BY transaction_date DESC, id DESC
            """,
            (current_user_id,)
        ).fetchall()

    finally:
        connection.close()

    data = [dict(row) for row in rows]

    df = pd.DataFrame(
        data,
        columns=[
            "id",
            "description",
            "transaction_type",
            "amount",
            "transaction_date"
        ]
    )

    if not df.empty:
        df["amount"] = pd.to_numeric(
            df["amount"],
            errors="coerce"
        ).fillna(0)

        df["transaction_date"] = pd.to_datetime(
            df["transaction_date"],
            errors="coerce"
        )

        df = df.dropna(
            subset=["transaction_date"]
        )

    return df


def update_transaction(
    transaction_id,
    description,
    transaction_type,
    amount,
    transaction_date
):
    """Update a transaction owned by the logged-in user."""

    connection = get_connection()

    try:
        connection.execute(
            """
            UPDATE transactions
            SET
                description = ?,
                transaction_type = ?,
                amount = ?,
                transaction_date = ?
            WHERE id = ?
            AND user_id = ?
            """,
            (
                description.strip(),
                transaction_type,
                float(amount),
                transaction_date.isoformat(),
                int(transaction_id),
                current_user_id
            )
        )

        connection.commit()

    finally:
        connection.close()


def delete_transaction(transaction_id):
    """Delete a transaction owned by the logged-in user."""

    connection = get_connection()

    try:
        connection.execute(
            """
            DELETE FROM transactions
            WHERE id = ?
            AND user_id = ?
            """,
            (
                int(transaction_id),
                current_user_id
            )
        )

        connection.commit()

    finally:
        connection.close()


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.markdown(
    """
    <div style="text-align:center; padding:15px 0 10px 0;">
        <div style="font-size:3rem;">💰</div>

        <h2 style="color:#FFFFFF; margin-bottom:0;">
            CashFlow Guardian
        </h2>

        <p style="color:#D9E2EC; font-size:0.9rem;">
            Protect your business cash flow
        </p>
    </div>

    <hr style="border:1px solid #D4AF37;">
    """,
    unsafe_allow_html=True
)

st.sidebar.success(
    f"Logged in as: {current_username}"
)

logout_button()

st.sidebar.markdown("---")

st.sidebar.markdown("### ⚙️ Business Settings")

business_name = st.sidebar.text_input(
    "Business name",
    value=saved_business_name
)

starting_cash = st.sidebar.number_input(
    "Starting cash (R)",
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
    options=[7, 14, 30, 60, 90],
    index=2,
    format_func=lambda days: f"{days} days"
)

st.sidebar.caption(
    "Business settings are currently session-based. "
    "They are not permanently saved to your account."
)


# ============================================================
# MAIN HEADER AND WELCOME BANNER
# ============================================================

safe_business_name = html.escape(
    str(business_name)
)

st.markdown(
    f"""
    <div class="welcome-banner">

        <div class="banner-icon">💰</div>

        <h2>Welcome to CashFlow Guardian</h2>

        <p>
            Protect your cash. Understand your spending.
            Build a stronger business.
        </p>

        <p style="margin-top:12px;">
            Business: <strong>{safe_business_name}</strong>
        </p>

    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    '<hr class="gold-line">',
    unsafe_allow_html=True
)


# ============================================================
# LOAD TRANSACTIONS
# ============================================================

transactions = get_transactions()

if transactions.empty:
    income_total = 0.0
    expense_total = 0.0

else:
    income_total = float(
        transactions.loc[
            transactions["transaction_type"] == "Income",
            "amount"
        ].sum()
    )

    expense_total = float(
        transactions.loc[
            transactions["transaction_type"] == "Expense",
            "amount"
        ].sum()
    )


# ============================================================
# CALCULATE CURRENT CASH
# ============================================================

current_cash = (
    starting_cash
    + income_total
    - expense_total
)


# ============================================================
# ANIMATED CASH COUNTER
# ============================================================

st.markdown(
    """
    <div class="cash-counter-card">

        <div class="cash-counter-label">
            💵 YOUR CURRENT CASH BALANCE
        </div>

        <div
            id="cashCounter"
            class="cash-counter-value"
            aria-live="polite"
        >
            R 0.00
        </div>

        <div class="cash-counter-caption">
            Your balance updates when your transactions change.
        </div>

    </div>
    """,
    unsafe_allow_html=True
)

# Use a separate HTML component for the animation.
# The exact balance is also displayed in the normal Streamlit
# metrics below, so the value remains available without JavaScript.

components.html(
    f"""
    <!DOCTYPE html>
    <html>
    <body style="margin:0; padding:0; height:0; overflow:hidden;">

    <script>
        (function() {{
            const target = {current_cash:.2f};
            const duration = 1200;
            const startTime = performance.now();

            const formatter = new Intl.NumberFormat("en-ZA", {{
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            }});

            function animateCounter(now) {{
                const element = window.parent.document
                    .getElementById("cashCounter");

                if (!element) {{
                    return;
                }}

                const progress = Math.min(
                    (now - startTime) / duration,
                    1
                );

                const easedProgress = 1 - Math.pow(
                    1 - progress,
                    3
                );

                const currentValue = target * easedProgress;

                element.textContent =
                    "R " + formatter.format(currentValue);

                if (progress < 1) {{
                    requestAnimationFrame(animateCounter);
                }} else {{
                    element.textContent =
                        "R " + formatter.format(target);
                }}
            }}

            requestAnimationFrame(animateCounter);
        }})();
    </script>

    </body>
    </html>
    """,
    height=0,
    scrolling=False
)


# ============================================================
# DASHBOARD METRICS
# ============================================================

st.markdown(
    '<p class="section-title">📊 Business Overview</p>',
    unsafe_allow_html=True
)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Starting Cash",
        value=f"R {starting_cash:,.2f}"
    )

with col2:
    st.metric(
        label="Total Income",
        value=f"R {income_total:,.2f}"
    )

with col3:
    st.metric(
        label="Total Expenses",
        value=f"R {expense_total:,.2f}"
    )

with col4:
    st.metric(
        label="Current Cash",
        value=f"R {current_cash:,.2f}",
        delta=f"R {current_cash - starting_cash:,.2f}"
    )


# ============================================================
# CASH HEALTH INDICATOR
# ============================================================

st.markdown("---")

st.markdown(
    '<p class="section-title">🛡️ Cash Health Indicator</p>',
    unsafe_allow_html=True
)

# This is a simple visual comparison with the warning limit.
# It is not a complete measure of business financial health.

if current_cash < 0:

    health_status = "Critical — Negative cash balance"
    health_colour = "#D93025"
    health_icon = "🚨"

elif current_cash <= warning_limit:

    health_status = "Needs attention — Low cash balance"
    health_colour = "#E09F1F"
    health_icon = "⚠️"

else:

    health_status = "Healthy — Above your warning limit"
    health_colour = "#087F5B"
    health_icon = "✅"


if warning_limit > 0:

    health_percentage = (
        current_cash / warning_limit
    ) * 100

    # Cap the bar between 0% and 100%.
    health_bar_width = max(
        0,
        min(100, health_percentage)
    )

    if current_cash < 0:
        health_bar_width = 0

    health_description = (
        f"Your balance is R {current_cash:,.2f}. "
        f"Your warning limit is R {warning_limit:,.2f}."
    )

else:

    # When the warning limit is zero, a percentage comparison
    # would be undefined. Use a simple positive/negative display.
    health_bar_width = 100 if current_cash > 0 else 0

    health_description = (
        f"Your balance is R {current_cash:,.2f}. "
        "Your warning limit is R 0.00."
    )


safe_health_status = html.escape(health_status)
safe_health_description = html.escape(health_description)

st.markdown(
    f"""
    <div class="health-card">

        <div class="health-heading">
            {health_icon} Cash Balance Status
        </div>

        <div class="health-description">
            {safe_health_description}
        </div>

        <div class="health-track">
            <div
                class="health-fill"
                style="
                    width:{health_bar_width:.2f}%;
                    background-color:{health_colour};
                "
            ></div>
        </div>

        <div
            class="health-status"
            style="color:{health_colour};"
        >
            {safe_health_status}
        </div>

    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# CASH FLOW STATUS
# ============================================================

st.markdown(
    '<p class="section-title">💡 Cash Flow Status</p>',
    unsafe_allow_html=True
)

if current_cash < 0:

    st.error(
        "🚨 Your current cash balance is negative! "
        "Review your expenses and expected income."
    )

elif current_cash <= warning_limit:

    st.warning(
        f"⚠️ Your current cash is R {current_cash:,.2f}. "
        f"This is at or below your warning limit of "
        f"R {warning_limit:,.2f}."
    )

else:

    st.success(
        f"✅ Your current cash is R {current_cash:,.2f}. "
        "It is above your low-cash warning limit."
    )


# ============================================================
# ADD A TRANSACTION
# ============================================================

st.markdown("---")

st.markdown(
    '<p class="section-title">➕ Add a Transaction</p>',
    unsafe_allow_html=True
)

with st.form("add_transaction_form", clear_on_submit=True):

    col1, col2 = st.columns(2)

    with col1:

        description = st.text_input(
            "Transaction description",
            placeholder="e.g. Selling groceries"
        )

        transaction_type = st.selectbox(
            "Transaction type",
            options=["Income", "Expense"]
        )

    with col2:

        amount = st.number_input(
            "Amount (R)",
            min_value=0.0,
            value=100.0,
            step=50.0
        )

        transaction_date = st.date_input(
            "Transaction date",
            value=date.today(),
            max_value=date.today()
        )

    submitted = st.form_submit_button(
        "💾 Save Transaction",
        use_container_width=True
    )

    if submitted:

        if not description.strip():

            st.error(
                "Please enter a description for the transaction."
            )

        elif amount <= 0:

            st.error(
                "The transaction amount must be greater than zero."
            )

        elif transaction_date > date.today():

            st.error(
                "Please choose today or an earlier date "
                "for a recorded transaction."
            )

        else:

            add_transaction(
                description,
                transaction_type,
                amount,
                transaction_date
            )

            st.success(
                "Transaction saved successfully!"
            )

            st.rerun()


# ============================================================
# CASH FLOW FORECAST
# ============================================================

st.markdown("---")

st.markdown(
    '<p class="section-title">🔮 Cash Flow Forecast</p>',
    unsafe_allow_html=True
)

st.write(
    f"This forecast estimates your cash balance for the next "
    f"{forecast_days} days using recorded transactions."
)

today = date.today()

forecast_dates = [
    today + timedelta(days=day)
    for day in range(forecast_days + 1)
]


# Calculate average daily net cash flow over the last 30 days.

historical_start = pd.Timestamp(
    today - timedelta(days=29)
)

historical_end = (
    pd.Timestamp(today)
    + pd.Timedelta(days=1)
    - pd.Timedelta(microseconds=1)
)

if transactions.empty:

    daily_net_average = 0.0

else:

    recent_transactions = transactions[
        (
            transactions["transaction_date"]
            >= historical_start
        )
        & (
            transactions["transaction_date"]
            <= historical_end
        )
    ].copy()

    if recent_transactions.empty:

        daily_net_average = 0.0

    else:

        recent_income = float(
            recent_transactions.loc[
                recent_transactions["transaction_type"] == "Income",
                "amount"
            ].sum()
        )

        recent_expenses = float(
            recent_transactions.loc[
                recent_transactions["transaction_type"] == "Expense",
                "amount"
            ].sum()
        )

        daily_net_average = (
            recent_income - recent_expenses
        ) / 30


forecast_rows = []

for day_number, forecast_date in enumerate(forecast_dates):

    projected_balance = (
        current_cash
        + daily_net_average * day_number
    )

    forecast_rows.append(
        {
            "Date": forecast_date,
            "Projected Cash (R)": round(
                projected_balance,
                2
            )
        }
    )


forecast_df = pd.DataFrame(forecast_rows)

final_projected_cash = float(
    forecast_df.iloc[-1]["Projected Cash (R)"]
)


# ============================================================
# FORECAST METRICS
# ============================================================

forecast_col1, forecast_col2 = st.columns(2)

with forecast_col1:

    st.metric(
        label=f"Projected Cash in {forecast_days} Days",
        value=f"R {final_projected_cash:,.2f}",
        delta=f"R {final_projected_cash - current_cash:,.2f}"
    )

with forecast_col2:

    st.metric(
        label="Estimated Average Daily Net Cash Flow",
        value=f"R {daily_net_average:,.2f}"
    )


st.caption(
    "Forecasts are estimates based on recent recorded net cash flow. "
    "They do not guarantee future income or expenses."
)


# ============================================================
# FORECAST WARNINGS
# ============================================================

lowest_projected_cash = float(
    forecast_df["Projected Cash (R)"].min()
)

if lowest_projected_cash < 0:

    negative_rows = forecast_df[
        forecast_df["Projected Cash (R)"] < 0
    ]

    first_negative = negative_rows.iloc[0]

    st.error(
        f"🚨 Warning: Your forecast estimates that cash may "
        f"become negative by "
        f"{first_negative['Date']:%d %B %Y}. "
        "Consider reducing expenses or increasing income."
    )

elif lowest_projected_cash <= warning_limit:

    st.warning(
        "⚠️ Your forecast shows that your cash may reach "
        "or fall below your warning limit. "
        "Plan for upcoming expenses."
    )

else:

    st.success(
        "✅ Your forecast remains above your low-cash warning "
        "limit for the selected period."
    )


# ============================================================
# FORECAST CHART
# ============================================================

st.markdown("### 📈 Projected Cash Balance")

chart_df = forecast_df.set_index("Date")

st.line_chart(
    chart_df,
    y="Projected Cash (R)",
    use_container_width=True
)


# ============================================================
# FORECAST TABLE
# ============================================================

with st.expander("📅 View Daily Forecast Details"):

    display_forecast = forecast_df.copy()

    display_forecast["Date"] = (
        display_forecast["Date"].apply(
            lambda value: value.strftime("%d %B %Y")
        )
    )

    display_forecast["Projected Cash (R)"] = (
        display_forecast["Projected Cash (R)"].apply(
            lambda value: f"R {value:,.2f}"
        )
    )

    st.dataframe(
        display_forecast,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# TRANSACTION HISTORY
# ============================================================

st.markdown("---")

st.markdown(
    '<p class="section-title">📋 Transaction History</p>',
    unsafe_allow_html=True
)

if transactions.empty:

    st.info(
        "You have not recorded any transactions yet. "
        "Add your first income or expense above."
    )

else:

    search_text = st.text_input(
        "🔍 Search transactions",
        placeholder="Search by description..."
    )

    filtered_transactions = transactions.copy()

    if search_text.strip():

        filtered_transactions = filtered_transactions[
            filtered_transactions["description"].str.contains(
                search_text.strip(),
                case=False,
                na=False,
                regex=False
            )
        ]

    display_transactions = filtered_transactions.copy()

    display_transactions["transaction_date"] = (
        display_transactions["transaction_date"].dt.strftime(
            "%d %B %Y"
        )
    )

    display_transactions = display_transactions.rename(
        columns={
            "id": "Transaction ID",
            "description": "Description",
            "transaction_type": "Type",
            "amount": "Amount (R)",
            "transaction_date": "Date"
        }
    )

    st.dataframe(
        display_transactions,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Amount (R)": st.column_config.NumberColumn(
                "Amount (R)",
                format="R %.2f"
            )
        }
    )


# ============================================================
# DOWNLOAD TRANSACTIONS
# ============================================================

if not transactions.empty:

    st.markdown("### 📥 Export Your Transactions")

    csv_df = transactions.copy()

    csv_df["transaction_date"] = (
        csv_df["transaction_date"].dt.strftime("%Y-%m-%d")
    )

    csv_df = csv_df.rename(
        columns={
            "id": "Transaction ID",
            "description": "Description",
            "transaction_type": "Type",
            "amount": "Amount (R)",
            "transaction_date": "Date"
        }
    )

    csv_data = csv_df.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        label="⬇️ Download Transactions as CSV",
        data=csv_data,
        file_name="cashflow_guardian_transactions.csv",
        mime="text/csv",
        use_container_width=True
    )


# ============================================================
# EDIT AND DELETE TRANSACTIONS
# ============================================================

st.markdown("---")

st.markdown(
    '<p class="section-title">✏️ Manage Transactions</p>',
    unsafe_allow_html=True
)

if transactions.empty:

    st.info(
        "Add a transaction before trying to edit or delete it."
    )

else:

    transaction_options = {}

    for _, row in transactions.iterrows():

        transaction_label = (
            f"#{int(row['id'])} | "
            f"{row['description']} | "
            f"{row['transaction_type']} | "
            f"R {row['amount']:,.2f} | "
            f"{row['transaction_date']:%d %b %Y}"
        )

        transaction_options[transaction_label] = int(
            row["id"]
        )

    selected_label = st.selectbox(
        "Select a transaction",
        options=list(transaction_options.keys())
    )

    selected_transaction_id = transaction_options[
        selected_label
    ]

    selected_rows = transactions[
        transactions["id"] == selected_transaction_id
    ]

    if not selected_rows.empty:

        selected_transaction = selected_rows.iloc[0]

        edit_tab, delete_tab = st.tabs(
            [
                "✏️ Edit Transaction",
                "🗑️ Delete Transaction"
            ]
        )

        # ----------------------------------------------------
        # EDIT TRANSACTION
        # ----------------------------------------------------

        with edit_tab:

            with st.form("edit_transaction_form"):

                edit_description = st.text_input(
                    "Description",
                    value=str(
                        selected_transaction["description"]
                    )
                )

                existing_type = str(
                    selected_transaction["transaction_type"]
                )

                edit_type = st.selectbox(
                    "Transaction type",
                    options=["Income", "Expense"],
                    index=(
                        0 if existing_type == "Income" else 1
                    )
                )

                edit_amount = st.number_input(
                    "Amount (R)",
                    min_value=0.01,
                    value=max(
                        0.01,
                        float(selected_transaction["amount"])
                    ),
                    step=50.0
                )

               
       edit_date = st.date_input(
    "Transaction date",
    value=selected_transaction["transaction_date"]
)


                save_changes = st.form_submit_button(
                    "💾 Save Changes",
                    use_container_width=True
                )

                if save_changes:

                    if not edit_description.strip():

                        st.error(
                            "The description cannot be empty."
                        )

                    elif edit_amount <= 0:

                        st.error(
                            "The amount must be greater than zero."
                        )

                    elif edit_date > date.today():

                        st.error(
                            "The date cannot be in the future."
                        )

                    else:

                        update_transaction(
                            selected_transaction_id,
                            edit_description,
                            edit_type,
                            edit_amount,
                            edit_date
                        )

                        st.success(
                            "Transaction updated successfully!"
                        )

                        st.rerun()

        # ----------------------------------------------------
        # DELETE TRANSACTION
        # ----------------------------------------------------

        with delete_tab:

            st.warning(
                "Deleting a transaction is permanent. "
                "Make sure you selected the correct transaction."
            )

            confirm_delete = st.checkbox(
                "I confirm that I want to delete this transaction."
            )

            if st.button(
                "🗑️ Delete Selected Transaction",
                use_container_width=True
            ):

                if confirm_delete:

                    delete_transaction(
                        selected_transaction_id
                    )

                    st.success(
                        "Transaction deleted successfully."
                    )

                    st.rerun()

                else:

                    st.error(
                        "Please tick the confirmation box before deleting."
                    )


# ============================================================
# BUSINESS SUMMARY
# ============================================================

st.markdown("---")

st.markdown(
    '<p class="section-title">📝 Business Summary</p>',
    unsafe_allow_html=True
)

summary_col1, summary_col2 = st.columns(2)

with summary_col1:

    st.markdown("#### 💵 Money In and Out")

    st.write(f"**Business:** {business_name}")

    st.write(
        f"**Total income:** R {income_total:,.2f}"
    )

    st.write(
        f"**Total expenses:** R {expense_total:,.2f}"
    )

    st.write(
        f"**Net recorded cash flow:** "
        f"R {income_total - expense_total:,.2f}"
    )

with summary_col2:

    st.markdown("#### 🎯 Cash Goals")

    st.write(
        f"**Current cash:** R {current_cash:,.2f}"
    )

    st.write(
        f"**Warning limit:** R {warning_limit:,.2f}"
    )

    cash_difference = current_cash - warning_limit

    if cash_difference >= 0:

        st.write(
            f"**Above warning limit by:** "
            f"R {cash_difference:,.2f}"
        )

    else:

        st.write(
            f"**Below warning limit by:** "
            f"R {abs(cash_difference):,.2f}"
        )


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.markdown(
    """
    <div class="footer">

        <strong>💰 CashFlow Guardian</strong>

        <br>

        Helping small businesses understand and protect their cash flow.

        <br><br>

        Built with Python, Streamlit and SQLite.

        <br>

        <span style="color:#D4AF37;">
            Plan smarter. Spend wisely. Grow confidently.
        </span>

    </div>
    """,
    unsafe_allow_html=True
)