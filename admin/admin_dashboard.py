# admin/admin_dashboard.py
import streamlit as st
import secrets
from db import get_connection
from auth.email_service import send_hr_verification_email
from utils.mail import send_email
from utils.templates import template_account_rejected


def admin_dashboard():
    inject_css()

    top_col1, top_col2, top_col3 = st.columns([7, 1, 1])
    with top_col1:
        st.markdown("<h1 class='title'>🛠️ Admin Dashboard</h1>", unsafe_allow_html=True)
        st.markdown("<p class='subtitle'>Review & Manage HR Approval Requests</p>", unsafe_allow_html=True)
    with top_col2:
        if st.button("🔄 Refresh", key="refresh_btn"):
            st.rerun()
    with top_col3:
        if st.button("Logout", key="logout_btn"):
            st.session_state.admin = None
            st.session_state.page = "home"
            st.success("Logged out!")
            st.rerun()

    # --- Handle Success/Error Messages from Session State ---
    if "admin_msg" in st.session_state:
        msg_text, msg_type = st.session_state.admin_msg
        if msg_type == "success": st.success(msg_text)
        elif msg_type == "error": st.error(msg_text)
        elif msg_type == "warning": st.warning(msg_text)
        del st.session_state.admin_msg

    hrs = []
    try:
        hrs = fetch_pending_hr()
        pass # fetched successfully
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return

    if not hrs:
        st.markdown("<div class='empty'>🎉 No pending HR approvals!</div>", unsafe_allow_html=True)
        return

    st.info(f"📋 There are {len(hrs)} pending HR account requests.")

    for user_id, name, email in hrs:
        render_hr_card(user_id, name, email)


def fetch_pending_hr():
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, name, email FROM users WHERE role='hr' AND status='pending_approval'")
        data = cur.fetchall()
        return data
    finally:
        conn.close()


def render_hr_card(user_id, name, email):
    with st.container():
        st.markdown(
            f"""
            <div class='card'>
                <div class='card-info'>
                    <div class='avatar'>👤</div>
                    <div>
                        <div class='name'>{name}</div>
                        <div class='email'>{email}</div>
                        <div class='badge-pending'>Pending Admin Approval</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        colA, colB = st.columns([1, 1])

        with colA:
            if st.button("Approve", key=f"approve_{user_id}"):
                sent, link = approve_hr(user_id, name, email)

                if sent:
                    st.session_state.admin_msg = (f"Approved {name} → Verification email sent ✅", "success")
                else:
                    st.session_state.admin_msg = (f"Approved {name}, but email failed. Link: {link}", "warning")

                st.rerun()

        with colB:
            if st.button("Reject", key=f"reject_{user_id}"):
                try:
                    reject_hr(user_id, name, email)
                    st.session_state.admin_msg = (f"Rejected {name} successfully.", "warning")
                except Exception as e:
                    st.session_state.admin_msg = (f"Failed to reject {name}: {e}", "error")
                st.rerun()

        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)


def approve_hr(user_id, name, email):
    # 1) Generate token
    verification_token = secrets.token_urlsafe(16)

    # 2) Save status + token in DB
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE users
        SET status='pending_hr_verification',
            verification_token=?
        WHERE id=?
    """, (verification_token, user_id))
    conn.commit()
    conn.close()

    # 3) Build link (same format as candidate)
    base_url = "http://localhost:8501"
    verification_link = f"{base_url}/?page=verify_email&token={verification_token}"

    # 4) Send HR verification email
    # Use your central email service to keep everything consistent
    try:
        send_hr_verification_email(email, name, verification_token)
        return True, verification_link
    except Exception:
        # If SMTP failed, return manual link fallback
        return False, verification_link


def reject_hr(user_id, name, email):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET status='rejected' WHERE id=?", (user_id,))
    conn.commit()
    conn.close()

    html = template_account_rejected(name, "HR")
    send_email(email, "Your HR Account has been Rejected", html)


def inject_css():
    st.markdown("""
    <style>

        .title {
            font-size: 28px;
            font-weight: 800;
            margin-bottom: -2px;
        }
        .subtitle {
            font-size: 15px;
            color: #777;
            margin-bottom: 12px;
        }

        .empty {
            padding: 18px;
            background: #e8f8e8;
            color: #2a682d;
            border-radius: 10px;
            text-align: center;
            font-weight: 600;
        }

        .card {
            background: rgba(255,255,255,0.75);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(210,210,210,0.5);
            border-radius: 14px;
            padding: 16px 20px;
            margin-bottom: 12px;
            transition: 0.25s;
        }
        .card:hover {
            transform: translateY(-3px);
            box-shadow: 0 6px 18px rgba(0,0,0,0.12);
        }

        .card-info {
            display: flex;
            align-items: center;
            gap: 14px;
        }
        .avatar {
            font-size: 32px;
            background: #ecf0f1;
            padding: 10px;
            border-radius: 50%;
        }
        .name {
            font-size: 18px;
            font-weight: 700;
        }
        .email {
            font-size: 14px;
            color: #555;
        }
        .badge-pending {
            margin-top: 3px;
            padding: 3px 8px;
            background: #ffa502;
            color: white;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 600;
            display: inline-block;
        }

        .divider {
            height: 1px;
            background: #e0e0e0;
            margin: 10px 0;
        }

        div[data-testid="column"] > div > div > button {
            width: 100% !important;
            height: 42px !important;
            display: flex !important;
            justify-content: center !important;
            align-items: center !important;
            padding: 0 !important;
            border-radius: 6px !important;
            border: none !important;
            color: white !important;
            font-size: 15px !important;
            font-weight: 600 !important;
        }

        div[data-testid="column"]:nth-of-type(1) button {
            background-color: #27ae60 !important;
        }
        div[data-testid="column"]:nth-of-type(1) button:hover {
            background-color: #1f8c4d !important;
        }

        div[data-testid="column"]:nth-of-type(2) button {
            background-color: #e74c3c !important;
        }
        div[data-testid="column"]:nth-of-type(2) button:hover {
            background-color: #c0392b !important;
        }

    </style>
    """, unsafe_allow_html=True)
