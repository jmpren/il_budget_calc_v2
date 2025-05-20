import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ─────────────────────────────────────────────
# App Configuration
# ─────────────────────────────────────────────
st.set_page_config(page_title="Illinois Budget Calculator v2", layout="wide")
st.title("Illinois Budget Calculator v2.0")

# ─────────────────────────────────────────────
# Load Data
# ─────────────────────────────────────────────
@st.cache_data

def load_data():
    df = pd.read_excel("data/budget_data.xlsx")
    df = df.dropna(subset=['Fund Category Name', 'Fund Name', 'FY25 Act Approp'])
    df['FY25 Act Approp'] = pd.to_numeric(df['FY25 Act Approp'], errors='coerce')
    df['FY25 Act Approp (M)'] = df['FY25 Act Approp'] / 1_000_000
    return df

df = load_data()

# Define fund categories considered revenue-generating
revenue_fund_cats = [
    "General Funds",
    "Highway Funds",
    "Special State Funds",
    "Federal Trust Funds"
]

# ─────────────────────────────────────────────
# Preprocess for Treemap and Adjustments
# ─────────────────────────────────────────────
grouped_df = df.groupby(['Fund Category Name', 'Fund Name'], as_index=False).agg({
    'FY25 Act Approp (M)': 'sum'
})

total_appropriation = grouped_df['FY25 Act Approp (M)'].sum()
grouped_df['Category Total'] = grouped_df.groupby('Fund Category Name')['FY25 Act Approp (M)'].transform('sum')
grouped_df['Category % of Total'] = grouped_df['Category Total'] / total_appropriation * 100
grouped_df['Fund % of Category'] = grouped_df['FY25 Act Approp (M)'] / grouped_df['Category Total'] * 100
grouped_df['Label Value'] = grouped_df['FY25 Act Approp (M)'].apply(lambda val: f"${val:,.0f}M")

# Fund category descriptions (for info tooltips)
category_info = {
    "General Funds": "This is the General Funds category.",
    "Highway Funds": "This is the Highway Funds category.",
    "Special State Funds": "This is the Special State Funds category.",
    "Federal Trust Funds": "This is the Federal Trust Funds category.",
    "Debt Service Funds": "This is the Debt Service Funds category.",
    "State Trust Funds": "This is the State Trust Funds category.",
    "Revolving Funds": "This is the Revolving Funds category.",
    "Bond Financed Funds": "This is the Bond Financed Funds category."
}

# ─────────────────────────────────────────────
# Main: Treemap
# ─────────────────────────────────────────────
st.subheader("FY25 Appropriations by Fund Category and Fund (in Millions)")

fig_tree = px.treemap(
    grouped_df,
    path=['Fund Category Name', 'Fund Name'],
    values='FY25 Act Approp (M)'
)

fig_tree.update_traces(
    texttemplate='%{label}<br>$%{value:,.0f}M',
    customdata=grouped_df[['Fund Category Name', 'Fund Name', 'Category % of Total', 'Fund % of Category']].values,
    hovertemplate=(
        "<b>Category:</b> %{customdata[0]}<br>" +
        "<b>Fund:</b> %{customdata[1]}<br>" +
        "<b>Category Share of Total:</b> %{customdata[2]:.1f}%<br>" +
        "<b>Fund Share of Category:</b> %{customdata[3]:.1f}%<br>" +
        "<extra></extra>"
    ),
    marker=dict(line=dict(color='white', width=1), cornerradius=5),
    textfont=dict(size=16)
)

st.plotly_chart(fig_tree, use_container_width=True)

# ─────────────────────────────────────────────
# Interactive Adjustments UI
# ─────────────────────────────────────────────
tab_spending, tab_revenue = st.tabs(["Adjust Spending", "Adjust Revenue"])

category_adjustments = {}
fund_adjustments = {}

spend_all = st.session_state.get("spend_all", 0.0)
rev_all = st.session_state.get("rev_all", 0.0)

with tab_spending:
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("### Adjust Spending by Fund Category")
    with col2:
        spend_all = st.number_input("Adjust All (%)", min_value=-100.0, max_value=100.0, value=spend_all, step=1.0, format="%.1f", key="spend_all")

    for category in grouped_df['Fund Category Name'].unique():
        label = f"{category}"
        if category in category_info:
            label += f"  ℹ️"
            st.markdown(f"<span style='display:inline-flex; align-items:center; gap:8px;'>"
            f"<b>{category}</b>"
            f"<span title='{category_info[category]}' style='cursor:help;'>"
            f"<span style='display:inline-block; width:16px; height:16px; border-radius:50%; border:1px solid #888; background-color:transparent; text-align:center; line-height:14px; font-size:12px;'>i</span>"
            f"</span></span>", unsafe_allow_html=True)
        cat_pct = st.number_input(
            f"{category} (% change)",
            min_value=-100.0,
            max_value=100.0,
            value=spend_all,
            step=1.0,
            format="%.1f",
            key=f"spend_cat_{category}"
        )
        category_adjustments[category] = cat_pct
        with st.expander(f"Drill down into {category}"):
            funds = grouped_df[grouped_df['Fund Category Name'] == category]['Fund Name'].unique()
            for fund in funds:
                fund_pct = st.number_input(
                    f"{fund} (% change)",
                    min_value=-100.0,
                    max_value=100.0,
                    value=0.0,
                    step=1.0,
                    format="%.1f",
                    key=f"spend_fund_{category}_{fund}"
                )
                if fund_pct != 0:
                    fund_adjustments[fund] = fund_pct

with tab_revenue:
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("### Adjust Revenue by Fund Category")
    with col2:
        rev_all = st.number_input("Adjust All (%)", min_value=-100.0, max_value=100.0, value=rev_all, step=1.0, format="%.1f", key="rev_all")

    for category in revenue_fund_cats:
        if category in category_info:
            st.markdown(f"<span style='display:inline-flex; align-items:center; gap:8px;'>"
            f"<b>{category}</b>"
            f"<span title='{category_info[category]}' style='cursor:help;'>"
            f"<span style='display:inline-block; width:16px; height:16px; border-radius:50%; border:1px solid #888; background-color:transparent; text-align:center; line-height:14px; font-size:12px;'>i</span>"
            f"</span></span>", unsafe_allow_html=True)
        cat_pct = st.number_input(
            f"{category} (% change)",
            min_value=-100.0,
            max_value=100.0,
            value=rev_all,
            step=1.0,
            format="%.1f",
            key=f"rev_cat_{category}"
        )
        category_adjustments[category] = cat_pct
        with st.expander(f"Drill down into {category}"):
            funds = grouped_df[grouped_df['Fund Category Name'] == category]['Fund Name'].unique()
            for fund in funds:
                fund_pct = st.number_input(
                    f"{fund} (% change)",
                    min_value=-100.0,
                    max_value=100.0,
                    value=0.0,
                    step=1.0,
                    format="%.1f",
                    key=f"rev_fund_{category}_{fund}"
                )
                if fund_pct != 0:
                    fund_adjustments[fund] = fund_pct

# ─────────────────────────────────────────────
# Calculate Totals
# ─────────────────────────────────────────────
adjusted_revenue = 0
adjusted_spending = 0

for _, row in grouped_df.iterrows():
    fund_cat = row['Fund Category Name']
    fund_name = row['Fund Name']
    value = row['FY25 Act Approp (M)']
    pct = fund_adjustments.get(fund_name, category_adjustments.get(fund_cat, 0))

    if fund_cat in revenue_fund_cats:
        adjusted_revenue += value * (1 + pct / 100)
    adjusted_spending += value * (1 + pct / 100)

original_revenue = df[df['Fund Category Name'].isin(revenue_fund_cats)]['FY25 Act Approp (M)'].sum()
original_spending = df['FY25 Act Approp (M)'].sum()
original_deficit = original_revenue - original_spending
adjusted_deficit = adjusted_revenue - adjusted_spending

# ─────────────────────────────────────────────
# Sidebar Budget Overview + Adjustment Log
# ─────────────────────────────────────────────
with st.sidebar:
    st.subheader("Budget Overview (in Billions)")

    for label, before, after in zip(
        ['Revenue', 'Spending', 'Deficit'],
        [original_revenue, original_spending, original_deficit],
        [adjusted_revenue, adjusted_spending, adjusted_deficit]
    ):
        st.markdown(f"**{label}**")

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=[before],
            y=['Before'],
            orientation='h',
            name='Before',
            text=[f"${before/1000:.2f}B"],
            textposition='auto',
            marker=dict(color='lightgray')
        ))
        fig.add_trace(go.Bar(
            x=[after],
            y=['After'],
            orientation='h',
            name='After',
            text=[f"${after/1000:.2f}B"],
            textposition='auto',
            marker=dict(color='steelblue')
        ))
        fig.update_layout(
            height=120,
            margin=dict(l=30, r=30, t=10, b=10),
            barmode='group',
            xaxis=dict(visible=False),
            yaxis=dict(showticklabels=True, title=''),
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Adjustment Log")
    any_changes = False
    for fund_cat, pct in category_adjustments.items():
        if pct != 0:
            color = 'green' if pct > 0 else 'red'
            st.markdown(f"**{fund_cat}:** <span style='color:{color}'>{pct:+.1f}%</span>", unsafe_allow_html=True)
            any_changes = True
    for fund_name, pct in fund_adjustments.items():
        color = 'green' if pct > 0 else 'red'
        st.markdown(f"**{fund_name}:** <span style='color:{color}'>{pct:+.1f}%</span>", unsafe_allow_html=True)
        any_changes = True
    if not any_changes:
        st.write("No adjustments yet.")

    if st.button("Reset All Adjustments"):
        for key in st.session_state.keys():
            del st.session_state[key]
        st.rerun()
