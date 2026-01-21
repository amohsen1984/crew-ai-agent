"""Analytics tab component."""

import matplotlib.pyplot as plt
import streamlit as st

from api_client import load_stats, load_tickets


def render_analytics():
    """Render the analytics tab."""
    st.header("Analytics")

    tickets_df = load_tickets()
    stats = load_stats()

    if tickets_df.empty:
        st.info("No data available for analytics.")
    else:
        # Classification distribution
        st.subheader("Classification Distribution")
        category_counts = tickets_df["category"].value_counts()
        fig, ax = plt.subplots()
        ax.pie(category_counts.values, labels=category_counts.index, autopct='%1.1f%%', startangle=90)
        ax.axis('equal')
        st.pyplot(fig)
        plt.close(fig)

        # Priority distribution
        st.subheader("Priority Distribution")
        priority_counts = tickets_df["priority"].value_counts()
        st.bar_chart(priority_counts)

        # Confidence score histogram
        st.subheader("Confidence Score Distribution")
        fig, ax = plt.subplots()
        ax.hist(tickets_df["confidence"].dropna(), bins=20, edgecolor='black')
        ax.set_xlabel("Confidence Score")
        ax.set_ylabel("Frequency")
        ax.set_title("Confidence Score Distribution")
        st.pyplot(fig)
        plt.close(fig)

        # Stats summary
        st.subheader("Summary Statistics")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Tickets", stats.get("total_tickets", 0))
        with col2:
            st.metric("Avg Confidence", f"{stats.get('avg_confidence', 0.0):.2%}")
        with col3:
            latest_metrics = stats.get("latest_metrics")
            if latest_metrics:
                st.metric("Last Processed", latest_metrics.get("total_processed", 0))


