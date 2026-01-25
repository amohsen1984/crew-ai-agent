"""QA Comparison tab component for comparing actual vs expected classifications."""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

from api_client import load_tickets, load_expected_classifications


def render_qa_comparison():
    """Render the QA comparison tab."""
    st.header("Quality Assurance - Classification Comparison")

    # Load data
    tickets_df = load_tickets()
    expected_df = load_expected_classifications()

    if tickets_df.empty:
        st.info("No generated tickets available. Run processing first.")
        return

    if expected_df.empty:
        st.warning("No expected classifications file found (data/expected_classifications.csv).")
        return

    # Merge actual and expected on source_id
    comparison_df = pd.merge(
        tickets_df[["source_id", "source_type", "category", "priority", "title", "confidence"]],
        expected_df[["source_id", "category", "priority", "suggested_title"]],
        on="source_id",
        how="inner",
        suffixes=("_actual", "_expected"),
    )

    if comparison_df.empty:
        st.warning("No matching records found between generated tickets and expected classifications.")
        return

    # Calculate matches
    comparison_df["category_match"] = comparison_df["category_actual"] == comparison_df["category_expected"]
    comparison_df["priority_match"] = comparison_df["priority_actual"] == comparison_df["priority_expected"]
    comparison_df["full_match"] = comparison_df["category_match"] & comparison_df["priority_match"]

    # Display summary metrics
    st.subheader("Accuracy Summary")

    total_records = len(comparison_df)
    category_accuracy = comparison_df["category_match"].mean() * 100
    priority_accuracy = comparison_df["priority_match"].mean() * 100
    full_accuracy = comparison_df["full_match"].mean() * 100

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Records", total_records)
    with col2:
        st.metric("Category Accuracy", f"{category_accuracy:.1f}%")
    with col3:
        st.metric("Priority Accuracy", f"{priority_accuracy:.1f}%")
    with col4:
        st.metric("Full Match Accuracy", f"{full_accuracy:.1f}%")

    # Accuracy by category
    st.subheader("Accuracy by Category")
    _render_category_accuracy(comparison_df)

    # Confusion matrix
    st.subheader("Category Confusion Matrix")
    _render_confusion_matrix(comparison_df)

    # Priority accuracy breakdown
    st.subheader("Priority Accuracy Breakdown")
    _render_priority_accuracy(comparison_df)

    # Detailed comparison table
    st.subheader("Detailed Comparison Table")
    _render_comparison_table(comparison_df)


def _render_category_accuracy(df: pd.DataFrame):
    """Render category accuracy bar chart."""
    category_stats = df.groupby("category_expected").agg(
        total=("category_match", "count"),
        correct=("category_match", "sum"),
    ).reset_index()
    category_stats["accuracy"] = (category_stats["correct"] / category_stats["total"]) * 100

    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.bar(category_stats["category_expected"], category_stats["accuracy"], color="steelblue")
    ax.axhline(y=100, color="green", linestyle="--", alpha=0.5, label="Perfect")
    ax.set_xlabel("Expected Category")
    ax.set_ylabel("Accuracy (%)")
    ax.set_title("Classification Accuracy by Category")
    ax.set_ylim(0, 110)

    # Add value labels on bars
    for bar, acc in zip(bars, category_stats["accuracy"]):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 2,
                f"{acc:.0f}%", ha="center", va="bottom", fontsize=9)

    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    # Show stats table
    st.dataframe(
        category_stats.rename(columns={
            "category_expected": "Category",
            "total": "Total",
            "correct": "Correct",
            "accuracy": "Accuracy (%)",
        }),
        hide_index=True,
    )


def _render_confusion_matrix(df: pd.DataFrame):
    """Render confusion matrix for category classification."""
    categories = sorted(set(df["category_expected"].unique()) | set(df["category_actual"].unique()))

    # Create confusion matrix
    matrix = pd.crosstab(
        df["category_actual"],
        df["category_expected"],
        rownames=["Actual"],
        colnames=["Expected"],
    ).reindex(index=categories, columns=categories, fill_value=0)

    fig, ax = plt.subplots(figsize=(10, 8))
    im = ax.imshow(matrix.values, cmap="Blues")

    # Add labels
    ax.set_xticks(np.arange(len(categories)))
    ax.set_yticks(np.arange(len(categories)))
    ax.set_xticklabels(categories)
    ax.set_yticklabels(categories)

    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")

    # Add text annotations
    for i in range(len(categories)):
        for j in range(len(categories)):
            value = matrix.values[i, j]
            text_color = "white" if value > matrix.values.max() / 2 else "black"
            ax.text(j, i, str(value), ha="center", va="center", color=text_color)

    ax.set_xlabel("Expected Category")
    ax.set_ylabel("Actual Category")
    ax.set_title("Category Classification Confusion Matrix")
    fig.colorbar(im, ax=ax, label="Count")
    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)


def _render_priority_accuracy(df: pd.DataFrame):
    """Render priority accuracy breakdown."""
    priority_order = ["Critical", "High", "Medium", "Low"]

    priority_stats = df.groupby("priority_expected").agg(
        total=("priority_match", "count"),
        correct=("priority_match", "sum"),
    ).reset_index()
    priority_stats["accuracy"] = (priority_stats["correct"] / priority_stats["total"]) * 100

    # Sort by priority order
    priority_stats["sort_order"] = priority_stats["priority_expected"].map(
        {p: i for i, p in enumerate(priority_order)}
    )
    priority_stats = priority_stats.sort_values("sort_order").drop(columns=["sort_order"])

    col1, col2 = st.columns(2)

    with col1:
        fig, ax = plt.subplots(figsize=(8, 5))
        colors = ["#d62728", "#ff7f0e", "#2ca02c", "#1f77b4"]  # Red, Orange, Green, Blue
        color_map = dict(zip(priority_order, colors))
        bar_colors = [color_map.get(p, "gray") for p in priority_stats["priority_expected"]]

        bars = ax.bar(priority_stats["priority_expected"], priority_stats["accuracy"], color=bar_colors)
        ax.axhline(y=100, color="green", linestyle="--", alpha=0.5)
        ax.set_xlabel("Expected Priority")
        ax.set_ylabel("Accuracy (%)")
        ax.set_title("Priority Classification Accuracy")
        ax.set_ylim(0, 110)

        for bar, acc in zip(bars, priority_stats["accuracy"]):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 2,
                    f"{acc:.0f}%", ha="center", va="bottom", fontsize=9)

        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

    with col2:
        # Priority confusion matrix (simplified)
        priority_matrix = pd.crosstab(
            df["priority_actual"],
            df["priority_expected"],
            rownames=["Actual"],
            colnames=["Expected"],
        )

        # Reorder
        for p in priority_order:
            if p not in priority_matrix.index:
                priority_matrix.loc[p] = 0
            if p not in priority_matrix.columns:
                priority_matrix[p] = 0
        priority_matrix = priority_matrix.reindex(index=priority_order, columns=priority_order, fill_value=0)

        fig, ax = plt.subplots(figsize=(6, 5))
        im = ax.imshow(priority_matrix.values, cmap="Oranges")

        ax.set_xticks(np.arange(len(priority_order)))
        ax.set_yticks(np.arange(len(priority_order)))
        ax.set_xticklabels(priority_order)
        ax.set_yticklabels(priority_order)

        for i in range(len(priority_order)):
            for j in range(len(priority_order)):
                value = priority_matrix.values[i, j]
                text_color = "white" if value > priority_matrix.values.max() / 2 else "black"
                ax.text(j, i, str(value), ha="center", va="center", color=text_color)

        ax.set_xlabel("Expected")
        ax.set_ylabel("Actual")
        ax.set_title("Priority Confusion Matrix")
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)


def _render_comparison_table(df: pd.DataFrame):
    """Render detailed comparison table with filtering."""
    # Filter options
    col1, col2, col3 = st.columns(3)
    with col1:
        show_filter = st.selectbox(
            "Show",
            ["All", "Matches Only", "Mismatches Only"],
            key="qa_filter",
        )
    with col2:
        category_filter = st.multiselect(
            "Filter by Expected Category",
            options=sorted(df["category_expected"].unique()),
            key="qa_category_filter",
        )
    with col3:
        priority_filter = st.multiselect(
            "Filter by Expected Priority",
            options=sorted(df["priority_expected"].unique()),
            key="qa_priority_filter",
        )

    # Apply filters
    filtered_df = df.copy()

    if show_filter == "Matches Only":
        filtered_df = filtered_df[filtered_df["full_match"]]
    elif show_filter == "Mismatches Only":
        filtered_df = filtered_df[~filtered_df["full_match"]]

    if category_filter:
        filtered_df = filtered_df[filtered_df["category_expected"].isin(category_filter)]

    if priority_filter:
        filtered_df = filtered_df[filtered_df["priority_expected"].isin(priority_filter)]

    # Prepare display dataframe
    display_df = filtered_df[[
        "source_id",
        "source_type",
        "category_expected",
        "category_actual",
        "category_match",
        "priority_expected",
        "priority_actual",
        "priority_match",
        "confidence",
    ]].copy()

    # Add status icons
    display_df["Category Status"] = display_df["category_match"].map({True: "✅", False: "❌"})
    display_df["Priority Status"] = display_df["priority_match"].map({True: "✅", False: "❌"})

    # Rename columns for display
    display_df = display_df.rename(columns={
        "source_id": "Source ID",
        "source_type": "Source Type",
        "category_expected": "Expected Category",
        "category_actual": "Actual Category",
        "priority_expected": "Expected Priority",
        "priority_actual": "Actual Priority",
        "confidence": "Confidence",
    })

    # Select columns to display
    display_columns = [
        "Source ID",
        "Source Type",
        "Expected Category",
        "Actual Category",
        "Category Status",
        "Expected Priority",
        "Actual Priority",
        "Priority Status",
        "Confidence",
    ]

    st.dataframe(
        display_df[display_columns],
        hide_index=True,
        use_container_width=True,
    )

    # Summary of filtered results
    st.caption(
        f"Showing {len(filtered_df)} of {len(df)} records. "
        f"Matches: {filtered_df['full_match'].sum()}, "
        f"Mismatches: {(~filtered_df['full_match']).sum()}"
    )
