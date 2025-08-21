import streamlit as st

st.set_page_config(page_title="Metric Test", layout="wide")

# Test the metric card rendering
st.markdown("""
<style>
.metric-card {
    background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
    color: white;
    border-radius: 16px;
    padding: 20px;
    margin: 10px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    transition: all 0.3s ease;
}

.metric-value {
    font-size: 2rem;
    font-weight: bold;
    margin-bottom: 8px;
}

.metric-label {
    font-size: 0.9rem;
    opacity: 0.9;
    margin-bottom: 8px;
}

.metric-container {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.icon-large {
    font-size: 2rem;
}
</style>
""", unsafe_allow_html=True)

def create_metric_card(title, value, icon, trend=None):
    """Create metric cards - simplified version for testing"""
    trend_html = ""
    if trend:
        trend_color = "#10b981" if trend > 0 else "#ef4444"
        trend_icon = "📈" if trend > 0 else "📉"
        trend_html = f"""
        <div style="color: {trend_color}; font-size: 0.8rem; margin-top: 4px;">
            {trend_icon} {abs(trend):.1f}% vs last month
        </div>
        """
    
    return f"""
    <div class="metric-card">
        <div class="metric-container">
            <div>
                <div class="metric-value">{value}</div>
                <div class="metric-label">{title}</div>
                {trend_html}
            </div>
            <div class="icon-large">{icon}</div>
        </div>
    </div>
    """

st.title("🧪 Metric Card Test")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(create_metric_card("Total Papers", 22, "📚", trend=5.2), unsafe_allow_html=True)

with col2:
    st.markdown(create_metric_card("Avg Citations", "0.0", "⭐", trend=2.1), unsafe_allow_html=True)

with col3:
    st.markdown(create_metric_card("Research Topics", 2, "🎯", trend=-1.3), unsafe_allow_html=True)

with col4:
    st.markdown(create_metric_card("Data Sources", 10, "🔗"), unsafe_allow_html=True)

st.markdown("---")
st.markdown("If you see properly styled blue cards above, the issue is elsewhere. If you see raw HTML, there's a rendering problem.")
