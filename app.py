import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ---------- Page Configuration ----------
st.set_page_config(
    page_title="CSV Data Quality Checker",
    page_icon="📊",
    layout="wide",
)

# ---------- Custom Styling ----------
st.markdown(
    """
    <style>
    .main-title {
        font-size: 4rem !important;
        font-weight: 800 !important;
        line-height: 1.2 !important;
        margin-bottom: 0.5rem !important;
    }
    .subtitle {
        color: #808495 !important;
        font-size: 1.25rem !important;
        margin-bottom: 1.5rem !important;
    }
    div[data-testid="stMetric"] {
        background-color: rgba(151, 166, 195, 0.15);
        border: 1px solid rgba(151, 166, 195, 0.25);
        border-radius: 10px;
        padding: 15px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Header ----------
st.markdown('<p class="main-title">📊 CSV Data Quality Checker</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="subtitle">Upload a CSV file to analyze its quality, '
    "spot missing data, find duplicates, and get an overall quality score.</p>",
    unsafe_allow_html=True,
)

# ---------- File Upload ----------
uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

if uploaded_file is None:
    st.info("👆 Upload a CSV file to get started.")
    st.stop()

# ---------- Load Data ----------
try:
    df = pd.read_csv(uploaded_file)
except Exception as e:
    st.error(f"Could not read the CSV file: {e}")
    st.stop()

if df.empty:
    st.warning("The uploaded CSV file is empty.")
    st.stop()

# ---------- Core Metrics ----------
row_count = len(df)
col_count = len(df.columns)
total_cells = row_count * col_count
missing_cells = int(df.isna().sum().sum())
duplicate_rows = int(df.duplicated().sum())

missing_pct = (missing_cells / total_cells) * 100 if total_cells else 0
duplicate_pct = (duplicate_rows / row_count) * 100 if row_count else 0

# ---------- Data Quality Score ----------
# Start at 100, subtract penalties for missing data and duplicates
quality_score = max(0, 100 - missing_pct - duplicate_pct)

# ---------- Metric Cards ----------
st.subheader("📋 Dataset Overview")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Rows", f"{row_count:,}")
c2.metric("Columns", f"{col_count:,}")
c3.metric("Missing Values", f"{missing_cells:,}", f"{missing_pct:.1f}% of cells", delta_color="inverse")
c4.metric("Duplicate Rows", f"{duplicate_rows:,}", f"{duplicate_pct:.1f}% of rows", delta_color="inverse")

# ---------- Data Preview ----------
st.subheader("🔍 Data Preview")
st.dataframe(df.head(50), use_container_width=True)

# ---------- Quality Score Gauge ----------
st.subheader("🏆 Data Quality Score")

if quality_score >= 90:
    score_color = "#2ecc71"   # green
    verdict = "Excellent — this dataset is clean and analysis-ready."
elif quality_score >= 70:
    score_color = "#f1c40f"   # yellow
    verdict = "Good — minor cleanup recommended before analysis."
else:
    score_color = "#e74c3c"   # red
    verdict = "Needs attention — significant cleaning required."

gauge = go.Figure(
    go.Indicator(
        mode="gauge+number",
        value=round(quality_score, 1),
        number={"suffix": " / 100"},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": score_color},
            "steps": [
                {"range": [0, 70], "color": "#fdecea"},
                {"range": [70, 90], "color": "#fef9e7"},
                {"range": [90, 100], "color": "#eafaf1"},
            ],
        },
    )
)
gauge.update_layout(height=300, margin=dict(t=40, b=20))

g1, g2 = st.columns([1, 1])
with g1:
    st.plotly_chart(gauge, use_container_width=True)
with g2:
    st.markdown("#### Verdict")
    st.write(verdict)
    st.markdown("**How the score works:**")
    st.write("- Starts at 100")
    st.write(f"- −{missing_pct:.1f} points for missing cells")
    st.write(f"- −{duplicate_pct:.1f} points for duplicate rows")

# ---------- Visualizations ----------
st.subheader("📈 Visual Analysis")

tab1, tab2, tab3 = st.tabs(["Missing Values", "Column Types", "Numeric Distributions"])

with tab1:
    missing_by_col = df.isna().sum().reset_index()
    missing_by_col.columns = ["Column", "Missing Count"]
    missing_by_col = missing_by_col[missing_by_col["Missing Count"] > 0]

    if missing_by_col.empty:
        st.success("No missing values found in any column. 🎉")
    else:
        fig = px.bar(
            missing_by_col.sort_values("Missing Count", ascending=True),
            x="Missing Count",
            y="Column",
            orientation="h",
            color="Missing Count",
            color_continuous_scale="Reds",
            title="Missing Values by Column",
        )
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    dtype_counts = df.dtypes.astype(str).value_counts().reset_index()
    dtype_counts.columns = ["Data Type", "Count"]
    fig = px.pie(
        dtype_counts,
        names="Data Type",
        values="Count",
        hole=0.45,
        title="Column Data Type Breakdown",
    )
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    if not numeric_cols:
        st.info("No numeric columns found in this dataset.")
    else:
        selected_col = st.selectbox("Choose a numeric column", numeric_cols)
        fig = px.histogram(
            df,
            x=selected_col,
            nbins=40,
            title=f"Distribution of {selected_col}",
            color_discrete_sequence=["#636efa"],
        )
        st.plotly_chart(fig, use_container_width=True)

# ---------- Column Details ----------
st.subheader("🧾 Column Details")
col_details = pd.DataFrame(
    {
        "Column": df.columns,
        "Data Type": df.dtypes.astype(str).values,
        "Missing": df.isna().sum().values,
        "Missing %": (df.isna().mean() * 100).round(1).values,
        "Unique Values": df.nunique().values,
    }
)
st.dataframe(col_details, use_container_width=True, hide_index=True)