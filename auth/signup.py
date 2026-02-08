# auth/signup.py
import streamlit as st
import re
from db import get_connection, hash_password
from auth.email_service import send_verification_email
from datetime import datetime
import secrets

# ---------- PUBLIC EMAIL BLOCK LIST (for HR company email rule) ----------
PUBLIC_EMAIL_DOMAINS = {
    "gmail.com", "googlemail.com",
    "yahoo.com", "yahoo.in",
    "outlook.com", "hotmail.com", "live.com",
    "icloud.com",
    "aol.com",
    "proton.me", "protonmail.com",
    "zoho.com",
    "gmx.com",
    "mail.com",
    "mailinator.com", "tempmail.com", "10minutemail.com", "guerrillamail.com"
}

def get_domain(email: str) -> str:
    return (email or "").split("@")[-1].strip().lower()

def is_public_domain(email: str) -> bool:
    return get_domain(email) in PUBLIC_EMAIL_DOMAINS

# ---------- VALIDATIONS ----------
def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email)

def is_strong_password(pw):
    return (
        len(pw) >= 8
        and re.search(r"[A-Z]", pw)
        and re.search(r"[a-z]", pw)
        and re.search(r"[0-9]", pw)
        and re.search(r"[!@#$%^&*]", pw)
    )

def signup_page():
    st.title("TrustHire Registration")

    # ---------- ROLE SELECTION ----------
    st.markdown("**Register As:**")
    role = st.selectbox(
        "Role",
        ["Select Role", "Candidate", "HR"],
        label_visibility="collapsed"
    )

    # ---------- SIGNUP FORM ----------
    with st.form("signup_form"):
        name = st.text_input("Full Name")
        email = st.text_input("Email ID")

        password = st.text_input("Password", type="password")
        retype_password = st.text_input("Retype Password", type="password")  # ✅ ADDED

        company_name = None
        company_location = None
        if role == "HR":
            company_name = st.text_input("Company Name")
            company_location = st.text_input("Company Location")

        submit = st.form_submit_button("Create Account")

        if submit:
            # ---------- BASIC VALIDATION ----------
            if role not in ["Candidate", "HR"]:
                st.error("Please select a valid role")
                return

            if not name or not email or not password or not retype_password:
                st.error("All fields are required")
                return

            # ✅ PASSWORD MATCH CHECK
            if password != retype_password:
                st.error("Passwords do not match")
                return

            if role == "HR" and (not company_name or not company_location):
                st.error("Company Name and Location are required for HR")
                return

            if not is_valid_email(email):
                st.error("Invalid email format")
                return

            # ✅ Block public emails for HR
            if role == "HR" and is_public_domain(email):
                st.error("HR must use a company email (public email providers are not allowed).")
                return

            if not is_strong_password(password):
                st.error(
                    "Password must be at least 8 characters and include "
                    "uppercase, lowercase, number, and special character"
                )
                return

            try:
                conn = get_connection()
                cur = conn.cursor()

                # ---------- DUPLICATE EMAIL CHECK ----------
                cur.execute(
                    "SELECT id FROM users WHERE LOWER(TRIM(email)) = LOWER(TRIM(?))",
                    (email.strip(),)
                )
                if cur.fetchone():
                    st.error("Email already registered")
                    conn.close()
                    return

                hashed_pw = hash_password(password)
                company_id = None

                # ---------- HR REGISTRATION ----------
                if role == "HR":
                    domain = get_domain(email)

                    cur.execute("SELECT id FROM companies WHERE LOWER(domain)=LOWER(?)", (domain,))
                    row = cur.fetchone()
                    if row:
                        company_id = row[0]
                    else:
                        cur.execute(
                            """
                            INSERT INTO companies (name, domain, city, status, created_at)
                            VALUES (?, ?, ?, ?, ?)
                            """,
                            (
                                company_name.strip(),
                                domain,
                                company_location.strip(),
                                "pending",
                                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            )
                        )
                        company_id = cur.lastrowid

                    user_status = "pending_approval"
                    verification_token = None

                # ---------- CANDIDATE REGISTRATION ----------
                else:
                    user_status = "pending_verification"
                    verification_token = secrets.token_urlsafe(16)

                # ---------- INSERT USER ----------
                cur.execute(
                    """
                    INSERT INTO users
                    (name, email, password, role, company_id, status, verification_token, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        name.strip(),
                        email.strip(),
                        hashed_pw,
                        role.lower(),
                        company_id,
                        user_status,
                        verification_token,
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    )
                )

                conn.commit()
                conn.close()

                # ---------- SUCCESS ----------
                if role == "HR":
                    st.success("✅ HR account created! Waiting for admin approval.")
                else:
                    try:
                        send_verification_email(email.strip(), name.strip(), verification_token)
                        st.success("✅ Candidate account created! Verification email sent.")
                    except Exception as e:
                        st.error(f"Candidate account created but failed to send email: {e}")

            except Exception as e:
                st.error(f"Registration failed: {e}")
