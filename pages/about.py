import streamlit as st

def show():
    st.markdown("""
        <div style='text-align: center; margin-bottom: 4rem;'>
            <h2 class="animate-soft" style="letter-spacing: 0.1em; color: var(--accent) !important;">MISSION_PROTOCOL</h2>
            <p class="text-dim mono" style="font-size: 0.85rem;">ARCHITECTURE_OVERVIEW_v1.0</p>
        </div>
    """, unsafe_allow_html=True)

    _, center_col, _ = st.columns([0.5, 3, 0.5])
    with center_col:
        with st.container(border=True):
            st.markdown("<p class='pill' style='margin-bottom: 2rem;'>CORE_OBJECTIVE</p>", unsafe_allow_html=True)
            st.markdown("""
                <h3 style='margin-top: 0; color: var(--text-primary) !important;'>TRUSTHIRE_FRAMEWORK</h3>
                <p style='font-size: 1.1rem; line-height: 1.8; opacity: 0.9; color: var(--text-secondary);'>
                    TrustHire is a secure recruitment and HR analytics infrastructure engineered to 
                    eliminate fraudulent credentials, automate profile validation, and optimize hiring 
                    quality through cryptographically sound verification protocols.
                </p>
                <div class='nm-divider' style='margin: 2.5rem 0;'></div>
                <p class='text-dim mono' style='font-size: 0.8rem; line-height: 1.6;'>
                    // SECURE_DATA_HANDLING_ACTIVE <br>
                    // INTEGRITY_CHECKS_ENABLED <br>
                    // DISTRIBUTED_TRUST_MODEL
                </p>
            """, unsafe_allow_html=True)
        
        st.markdown("<div style='height: 4rem;'></div>", unsafe_allow_html=True)
        if st.button("<< RETURN_TO_BASE", key="back_from_about", use_container_width=True):
            st.session_state.page = "home"
            st.rerun()
