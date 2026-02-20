import streamlit as st

def display_match_result(score, missing):
    st.subheader("🎯 Job Match Result")

    st.progress(int(score))
    st.success(f"Match Score: {score:.0f}%")

    if missing:
        st.warning("Missing Skills:")
        for skill in missing:
            st.write("•", skill)
    else:
        st.success("✅ You match all required skills!")