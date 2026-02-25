import streamlit as st

def show():
    st.markdown("""
        <div style='text-align: center; margin-top: 5rem; margin-bottom: 4rem;'>
            <h2 class="animate-soft" style="letter-spacing: 0.1em; color: var(--accent) !important;">COMMUNICATION_CHANNELS</h2>
            <p class="text-dim mono" style="font-size: 0.85rem;">ESTABLISHING_EXTERNAL_LINK</p>
        </div>
    """, unsafe_allow_html=True)

    _, center_col, _ = st.columns([0.8, 2.4, 0.8])
    with center_col:
        with st.container(border=True):
            st.markdown("<p class='pill' style='margin-bottom: 2.5rem;'>NETWORK_ROUTING</p>", unsafe_allow_html=True)
            
            c_info, c_action = st.columns([2, 1])
            with c_info:
                st.markdown("""
                    <h3 style='margin-top: 0; margin-bottom: 1.5rem; color: var(--text-primary) !important;'>CLIENT_SUPPORT_MATRIX</h3>
                    <div class="mono" style="font-size: 0.95rem; line-height: 2.4; color: var(--text-secondary);">
                        <span class="text-dim">SECURE_MAILBOX:</span> &nbsp;&nbsp;support@trusthire.com<br>
                        <span class="text-dim">VOIP_RELAY:</span> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;+91 12345 67890<br>
                        <span class="text-dim">WEB_GATEWAY:</span> &nbsp;&nbsp;&nbsp;&nbsp;www.trusthire.com<br>
                        <span class="text-dim">GEO_COORDS:</span> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;BANGALORE_IN
                    </div>
                """, unsafe_allow_html=True)
            
            with c_action:
                st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
                st.markdown("""
                    <div class='nm-inset' style='padding: 1.5rem; text-align: center; border-radius: var(--radius-sm);'>
                        <span class='text-dim mono' style='font-size: 0.7rem;'>PING_RESPONSE</span><br>
                        <span style='font-weight: 800; font-size: 1.2rem; color: var(--success);'>12ms</span>
                    </div>
                """, unsafe_allow_html=True)
                
            st.markdown("<div class='nm-divider' style='margin: 3rem 0 2rem 0;'></div>", unsafe_allow_html=True)
            
            if st.button("<< TERMINATE_LINK_PROTOCOLS", key="back_from_contact", use_container_width=True):
                st.session_state.page = "home"
                st.rerun()
