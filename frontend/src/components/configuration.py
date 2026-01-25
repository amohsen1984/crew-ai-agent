"""Configuration Panel tab component."""

import os
import streamlit as st

from api_client import set_priority_rules, get_priority_rules


def render_configuration():
    """Render the configuration panel tab."""
    st.header("Configuration Panel")
    
    # Load priority rules from backend on initialization
    if "priority_rules_loaded" not in st.session_state:
        backend_rules = get_priority_rules()
        if backend_rules:
            st.session_state.priority_rules = backend_rules
        st.session_state.priority_rules_loaded = True

    st.subheader("Processing Settings")
    st.text_input("LLM Model", value=os.getenv("MODEL_NAME", "gpt-4"), disabled=True)
    
    # Initialize classification threshold in session state if not present
    if "classification_threshold" not in st.session_state:
        st.session_state.classification_threshold = 0.7
    
    classification_threshold = st.slider(
        "Classification Threshold",
        min_value=0.5,
        max_value=0.9,
        value=st.session_state.classification_threshold,
        step=0.05,
        help="Minimum confidence score required for classification (0.5-0.9). Lower values accept more classifications, higher values are more strict."
    )
    
    # Update session state when threshold changes
    if classification_threshold != st.session_state.classification_threshold:
        st.session_state.classification_threshold = classification_threshold
        st.info(f"Classification threshold set to {classification_threshold}. This will be used for the next processing run.")

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
        bug_critical_keywords = st.text_input(
            "Critical Keywords (comma-separated)",
            value=", ".join(
                st.session_state.priority_rules["Bug"].get("critical_keywords", [])
            ),
            key="bug_critical_keywords",
        )
        bug_high_keywords = st.text_input(
            "High Keywords (comma-separated)",
            value=", ".join(
                st.session_state.priority_rules["Bug"].get("high_keywords", [])
            ),
            key="bug_high_keywords",
        )
        bug_medium_keywords = st.text_input(
            "Medium Keywords (comma-separated)",
            value=", ".join(
                st.session_state.priority_rules["Bug"].get("medium_keywords", [])
            ),
            key="bug_medium_keywords",
        )
        bug_low_keywords = st.text_input(
            "Low Keywords (comma-separated)",
            value=", ".join(
                st.session_state.priority_rules["Bug"].get("low_keywords", [])
            ),
            key="bug_low_keywords",
        )
        if st.button("Save Bug Rules", key="save_bug"):
            bug_rules = {
                "default": bug_default,
                "critical_keywords": [k.strip() for k in bug_critical_keywords.split(",") if k.strip()],
                "high_keywords": [k.strip() for k in bug_high_keywords.split(",") if k.strip()],
                "medium_keywords": [k.strip() for k in bug_medium_keywords.split(",") if k.strip()],
                "low_keywords": [k.strip() for k in bug_low_keywords.split(",") if k.strip()],
            }
            # Ensure all categories exist in session state before updating
            if "Bug" not in st.session_state.priority_rules:
                st.session_state.priority_rules["Bug"] = {}
            st.session_state.priority_rules["Bug"] = bug_rules
            # Send to backend (backend will merge with existing/defaults for other categories)
            result = set_priority_rules(st.session_state.priority_rules)
            if result.get("status") == "success":
                st.success("Bug priority rules saved and sent to backend!")
                # Reload from backend to get merged rules
                backend_rules = get_priority_rules()
                if backend_rules:
                    st.session_state.priority_rules = backend_rules
            else:
                st.error(f"Failed to save to backend: {result.get('error', 'Unknown error')}")

    with st.expander("Feature Request Priority Rules"):
        feature_default = st.selectbox(
            "Default Priority",
            ["Critical", "High", "Medium", "Low"],
            index=["Critical", "High", "Medium", "Low"].index(
                st.session_state.priority_rules["Feature Request"]["default"]
            ),
            key="feature_default",
        )
        feature_critical_keywords = st.text_input(
            "Critical Keywords (comma-separated)",
            value=", ".join(
                st.session_state.priority_rules["Feature Request"].get("critical_keywords", [])
            ),
            key="feature_critical_keywords",
        )
        feature_high_keywords = st.text_input(
            "High Keywords (comma-separated)",
            value=", ".join(
                st.session_state.priority_rules["Feature Request"].get("high_keywords", [])
            ),
            key="feature_high_keywords",
        )
        feature_medium_keywords = st.text_input(
            "Medium Keywords (comma-separated)",
            value=", ".join(
                st.session_state.priority_rules["Feature Request"].get("medium_keywords", [])
            ),
            key="feature_medium_keywords",
        )
        feature_low_keywords = st.text_input(
            "Low Keywords (comma-separated)",
            value=", ".join(
                st.session_state.priority_rules["Feature Request"].get("low_keywords", [])
            ),
            key="feature_low_keywords",
        )
        if st.button("Save Feature Rules", key="save_feature"):
            feature_rules = {
                "default": feature_default,
                "critical_keywords": [k.strip() for k in feature_critical_keywords.split(",") if k.strip()],
                "high_keywords": [k.strip() for k in feature_high_keywords.split(",") if k.strip()],
                "medium_keywords": [k.strip() for k in feature_medium_keywords.split(",") if k.strip()],
                "low_keywords": [k.strip() for k in feature_low_keywords.split(",") if k.strip()],
            }
            # Ensure all categories exist in session state before updating
            if "Feature Request" not in st.session_state.priority_rules:
                st.session_state.priority_rules["Feature Request"] = {}
            st.session_state.priority_rules["Feature Request"] = feature_rules
            # Send to backend (backend will merge with existing/defaults for other categories)
            result = set_priority_rules(st.session_state.priority_rules)
            if result.get("status") == "success":
                st.success("Feature Request priority rules saved and sent to backend!")
                # Reload from backend to get merged rules
                backend_rules = get_priority_rules()
                if backend_rules:
                    st.session_state.priority_rules = backend_rules
            else:
                st.error(f"Failed to save to backend: {result.get('error', 'Unknown error')}")

    with st.expander("Complaint Priority Rules"):
        complaint_default = st.selectbox(
            "Default Priority",
            ["Critical", "High", "Medium", "Low"],
            index=["Critical", "High", "Medium", "Low"].index(
                st.session_state.priority_rules["Complaint"]["default"]
            ),
            key="complaint_default",
        )
        complaint_critical_keywords = st.text_input(
            "Critical Keywords (comma-separated)",
            value=", ".join(
                st.session_state.priority_rules["Complaint"].get("critical_keywords", [])
            ),
            key="complaint_critical_keywords",
        )
        complaint_high_keywords = st.text_input(
            "High Keywords (comma-separated)",
            value=", ".join(
                st.session_state.priority_rules["Complaint"].get("high_keywords", [])
            ),
            key="complaint_high_keywords",
        )
        complaint_medium_keywords = st.text_input(
            "Medium Keywords (comma-separated)",
            value=", ".join(
                st.session_state.priority_rules["Complaint"].get("medium_keywords", [])
            ),
            key="complaint_medium_keywords",
        )
        complaint_low_keywords = st.text_input(
            "Low Keywords (comma-separated)",
            value=", ".join(
                st.session_state.priority_rules["Complaint"].get("low_keywords", [])
            ),
            key="complaint_low_keywords",
        )
        if st.button("Save Complaint Rules", key="save_complaint"):
            complaint_rules = {
                "default": complaint_default,
                "critical_keywords": [k.strip() for k in complaint_critical_keywords.split(",") if k.strip()],
                "high_keywords": [k.strip() for k in complaint_high_keywords.split(",") if k.strip()],
                "medium_keywords": [k.strip() for k in complaint_medium_keywords.split(",") if k.strip()],
                "low_keywords": [k.strip() for k in complaint_low_keywords.split(",") if k.strip()],
            }
            # Ensure all categories exist in session state before updating
            if "Complaint" not in st.session_state.priority_rules:
                st.session_state.priority_rules["Complaint"] = {}
            st.session_state.priority_rules["Complaint"] = complaint_rules
            # Send to backend (backend will merge with existing/defaults for other categories)
            result = set_priority_rules(st.session_state.priority_rules)
            if result.get("status") == "success":
                st.success("Complaint priority rules saved and sent to backend!")
                # Reload from backend to get merged rules
                backend_rules = get_priority_rules()
                if backend_rules:
                    st.session_state.priority_rules = backend_rules
            else:
                st.error(f"Failed to save to backend: {result.get('error', 'Unknown error')}")


