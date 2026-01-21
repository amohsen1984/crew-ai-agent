"""Configuration Panel tab component."""

import os
import streamlit as st


def render_configuration():
    """Render the configuration panel tab."""
    st.header("Configuration Panel")

    st.subheader("Processing Settings")
    st.text_input("LLM Model", value=os.getenv("MODEL_NAME", "gpt-4"), disabled=True)
    st.slider("Classification Threshold", 0.5, 0.9, 0.7, 0.05, disabled=True)

    st.divider()

    st.subheader("Priority Override Rules")
    # Same as before - these are frontend-only settings
    with st.expander("Bug Priority Rules"):
        bug_default = st.selectbox(
            "Default Priority",
            ["Critical", "High", "Medium", "Low"],
            index=["Critical", "High", "Medium", "Low"].index(
                st.session_state.priority_rules["Bug"]["default"]
            ),
            key="bug_default",
        )
        bug_keywords = st.text_input(
            "Critical Keywords (comma-separated)",
            value=", ".join(
                st.session_state.priority_rules["Bug"]["critical_keywords"]
            ),
            key="bug_keywords",
        )
        if st.button("Save Bug Rules", key="save_bug"):
            st.session_state.priority_rules["Bug"] = {
                "default": bug_default,
                "critical_keywords": [k.strip() for k in bug_keywords.split(",")],
            }
            st.success("Bug priority rules saved!")

    with st.expander("Feature Request Priority Rules"):
        feature_default = st.selectbox(
            "Default Priority",
            ["Critical", "High", "Medium", "Low"],
            index=["Critical", "High", "Medium", "Low"].index(
                st.session_state.priority_rules["Feature Request"]["default"]
            ),
            key="feature_default",
        )
        feature_keywords = st.text_input(
            "High Demand Keywords (comma-separated)",
            value=", ".join(
                st.session_state.priority_rules["Feature Request"][
                    "high_demand_keywords"
                ]
            ),
            key="feature_keywords",
        )
        if st.button("Save Feature Rules", key="save_feature"):
            st.session_state.priority_rules["Feature Request"] = {
                "default": feature_default,
                "high_demand_keywords": [
                    k.strip() for k in feature_keywords.split(",")
                ],
            }
            st.success("Feature Request priority rules saved!")

    with st.expander("Complaint Priority Rules"):
        complaint_default = st.selectbox(
            "Default Priority",
            ["Critical", "High", "Medium", "Low"],
            index=["Critical", "High", "Medium", "Low"].index(
                st.session_state.priority_rules["Complaint"]["default"]
            ),
            key="complaint_default",
        )
        complaint_keywords = st.text_input(
            "High Priority Keywords (comma-separated)",
            value=", ".join(
                st.session_state.priority_rules["Complaint"]["high_keywords"]
            ),
            key="complaint_keywords",
        )
        if st.button("Save Complaint Rules", key="save_complaint"):
            st.session_state.priority_rules["Complaint"] = {
                "default": complaint_default,
                "high_keywords": [
                    k.strip() for k in complaint_keywords.split(",")
                ],
            }
            st.success("Complaint priority rules saved!")


