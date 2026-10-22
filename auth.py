
import sqlite3
import bcrypt
import streamlit as st

from pathlib import Path

DATABASE = Path(__file__).resolve().parent / "cashflow.db"


def get_auth_connection():
    return sqlite3.connect(DATABASE)


def create_users_table():
    with get_auth_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                business_name TEXT NOT NULL,
                password_hash BLOB NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)


def register_user(username, business_name, password):
    username = username.strip().lower()
    business_name = business_name.strip()

    if not username or not business_name or not password:
        return False, "Please complete all fields."

    if len(username) < 3:
        return False, "Your username must contain at least 3 characters."

    if len(password) < 12:
        return False, "Your password must contain at least 12 characters."

    if len(password.encode("utf-8")) > 72:
        return False, "Please use a password of no more than 72 UTF-8 bytes."

    password_hash = bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    )

    try:
        with get_auth_connection() as conn:
            conn.execute("""
                INSERT INTO users
                (username, business_name, password_hash)
                VALUES (?, ?, ?)
            """, (username, business_name, password_hash))

        return True, "Account created successfully. You can now log in."

    except sqlite3.IntegrityError:
        return False, "That username is already registered."


def authenticate_user(username, password):
    username = username.strip().lower()

    with get_auth_connection() as conn:
        user = conn.execute("""
            SELECT id, username, business_name, password_hash
            FROM users
            WHERE username = ?
        """, (username,)).fetchone()

    if user is None:
        return None

    stored_hash = user[3]

    try:
        password_is_correct = bcrypt.checkpw(
            password.encode("utf-8"),
            stored_hash
        )
    except (ValueError, TypeError):
        return None

    if not password_is_correct:
        return None

    return {
        "id": user[0],
        "username": user[1],
        "business_name": user[2]
    }


def show_auth_page():
    st.title("💰 CashFlow Guardian")
    st.write("Manage your business cash flow securely.")

    login_tab, register_tab = st.tabs(["Log in", "Create account"])

    with login_tab:
        with st.form("login_form"):
            username = st.text_input("Username", key="login_username")
            password = st.text_input(
                "Password",
                type="password",
                key="login_password"
            )

            login_clicked = st.form_submit_button(
                "Log in",
                use_container_width=True
            )

        if login_clicked:
            if not username.strip() or not password:
                st.error("Enter your username and password.")
            else:
                user = authenticate_user(username, password)

                if user:
                    st.session_state["user"] = user
                    st.rerun()
                else:
                    st.error("Incorrect username or password.")

    with register_tab:
        with st.form("register_form"):
            new_username = st.text_input(
                "Choose a username",
                key="register_username"
            )

            business_name = st.text_input(
                "Business name",
                key="register_business"
            )

            new_password = st.text_input(
                "Create a password (at least 12 characters)",
                type="password",
                key="register_password"
            )

            confirm_password = st.text_input(
                "Confirm password",
                type="password",
                key="confirm_password"
            )

            register_clicked = st.form_submit_button(
                "Create account",
                use_container_width=True
            )

        if register_clicked:
            if new_password != confirm_password:
                st.error("The passwords do not match.")
            else:
                success, message = register_user(
                    new_username,
                    business_name,
                    new_password
                )

                if success:
                    st.success(message)
                else:
                    st.error(message)



def logout_button():
    if st.button("Log out", use_container_width=True):
        st.session_state.pop("user", None)
        st.rerun()

create_users_table()
