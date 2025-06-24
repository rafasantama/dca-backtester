"""Dark theme CSS styles for the DCA Backtester wizard."""

import streamlit as st

DARK_THEME_CSS = """
<style>
/* Dark Theme Design System */

/* Reset and Base Styles */
* {
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
    line-height: 1.6;
    color: #e9ecef;
    background-color: #0d1117;
}

/* Typography */
.wizard-header {
    font-size: 2.5rem;
    font-weight: 700;
    color: #58a6ff;
    text-align: center;
    margin-bottom: 0.5rem;
}

.wizard-subtitle {
    font-size: 1.125rem;
    color: #8b949e;
    text-align: center;
    margin-bottom: 2rem;
}

.step-title {
    font-size: 1.75rem;
    font-weight: 600;
    color: #e9ecef;
    margin-bottom: 0.5rem;
}

.step-description {
    font-size: 1rem;
    color: #8b949e;
    margin-bottom: 2rem;
}

.section-title {
    font-size: 1.25rem;
    font-weight: 600;
    color: #e9ecef;
    margin-bottom: 1rem;
}

/* Cards */
.summary-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 0.375rem;
    padding: 1.5rem;
    text-align: center;
    box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.3);
    transition: all 0.15s ease-in-out;
    margin-bottom: 1rem;
}

.summary-card:hover {
    box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.4);
    transform: translateY(-2px);
    border-color: #58a6ff;
}

.summary-card h4 {
    font-size: 0.875rem;
    color: #8b949e;
    margin-bottom: 0.5rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    font-weight: 600;
}

.summary-card p {
    font-weight: 700;
    font-size: 1.25rem;
    color: #e9ecef;
    margin: 0;
}

/* Progress Steps */
.progress-container {
    background: #161b22;
    border-radius: 0.375rem;
    padding: 1rem;
    margin: 1rem 0;
    border: 1px solid #30363d;
}

.progress-step {
    display: inline-block;
    padding: 0.5rem 1rem;
    margin: 0 0.25rem;
    border-radius: 0.375rem;
    font-weight: 500;
    font-size: 0.875rem;
    transition: all 0.15s ease-in-out;
}

.progress-step.active {
    background: #58a6ff;
    color: #0d1117;
}

.progress-step.completed {
    background: #238636;
    color: #e9ecef;
}

.progress-step.pending {
    background: #21262d;
    color: #8b949e;
    border: 1px solid #30363d;
}

/* Buttons */
.btn-primary {
    background: #58a6ff;
    color: #0d1117;
    border: none;
    border-radius: 0.375rem;
    padding: 0.75rem 1.5rem;
    font-weight: 600;
    font-size: 0.875rem;
    cursor: pointer;
    transition: all 0.15s ease-in-out;
    text-decoration: none;
    display: inline-block;
}

.btn-primary:hover {
    background: #79c0ff;
    transform: translateY(-1px);
    box-shadow: 0 0.25rem 0.5rem rgba(88, 166, 255, 0.3);
}

.btn-secondary {
    background: #21262d;
    color: #e9ecef;
    border: 1px solid #30363d;
    border-radius: 0.375rem;
    padding: 0.75rem 1.5rem;
    font-weight: 600;
    font-size: 0.875rem;
    cursor: pointer;
    transition: all 0.15s ease-in-out;
    text-decoration: none;
    display: inline-block;
}

.btn-secondary:hover {
    background: #30363d;
    border-color: #58a6ff;
}

/* Metrics */
.metric-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 0.375rem;
    padding: 1.5rem;
    text-align: center;
    box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.3);
    margin-bottom: 1rem;
}

.metric-value {
    font-weight: 700;
    font-size: 1.5rem;
    color: #e9ecef;
    margin-bottom: 0.25rem;
}

.metric-label {
    font-weight: 500;
    font-size: 0.875rem;
    color: #8b949e;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

/* Insights */
.insight-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 0.375rem;
    padding: 1.5rem;
    margin-bottom: 1rem;
    box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.3);
}

.insight-title {
    font-weight: 600;
    font-size: 1rem;
    color: #e9ecef;
    margin-bottom: 0.5rem;
}

.insight-content {
    font-weight: 400;
    font-size: 0.875rem;
    color: #8b949e;
    line-height: 1.5;
}

/* Alerts */
.alert {
    padding: 1rem;
    border-radius: 0.375rem;
    margin-bottom: 1rem;
    border: 1px solid transparent;
}

.alert-success {
    background-color: #0d4429;
    border-color: #238636;
    color: #7ee787;
}

.alert-warning {
    background-color: #3d2300;
    border-color: #f0883e;
    color: #f0883e;
}

.alert-danger {
    background-color: #3d1e1e;
    border-color: #f85149;
    color: #f85149;
}

.alert-info {
    background-color: #0c2d6b;
    border-color: #58a6ff;
    color: #79c0ff;
}

/* Responsive Design */
@media (max-width: 768px) {
    .wizard-header {
        font-size: 2rem;
    }
    
    .wizard-subtitle {
        font-size: 1rem;
    }
    
    .step-title {
        font-size: 1.5rem;
    }
    
    .summary-card {
        padding: 1rem;
    }
    
    .metric-card {
        padding: 1rem;
    }
}

/* Streamlit Overrides */
.stApp {
    background-color: #0d1117 !important;
}

.main .block-container {
    background-color: #0d1117 !important;
}

/* Hide Streamlit elements */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Input styling for dark theme */
.stTextInput > div > div > input {
    background-color: #21262d !important;
    color: #e9ecef !important;
    border-color: #30363d !important;
}

.stSelectbox > div > div > div {
    background-color: #21262d !important;
    color: #e9ecef !important;
}

.stDateInput > div > div > input {
    background-color: #21262d !important;
    color: #e9ecef !important;
    border-color: #30363d !important;
}

.stNumberInput > div > div > input {
    background-color: #21262d !important;
    color: #e9ecef !important;
    border-color: #30363d !important;
}

/* Expander styling for dark theme */
.streamlit-expanderHeader {
    background-color: #161b22 !important;
    border: 1px solid #30363d !important;
    color: #e9ecef !important;
    border-radius: 0.375rem !important;
    padding: 1rem !important;
    font-weight: 600 !important;
}

.streamlit-expanderHeader:hover {
    background-color: #21262d !important;
    border-color: #58a6ff !important;
}

.streamlit-expanderContent {
    background-color: #161b22 !important;
    border: 1px solid #30363d !important;
    border-top: none !important;
    border-radius: 0 0 0.375rem 0.375rem !important;
    padding: 1rem !important;
}

/* Dataframe styling for dark theme */
.dataframe {
    background-color: #161b22 !important;
    color: #e9ecef !important;
}

.dataframe th {
    background-color: #21262d !important;
    color: #e9ecef !important;
    border-color: #30363d !important;
}

.dataframe td {
    background-color: #161b22 !important;
    color: #e9ecef !important;
    border-color: #30363d !important;
}
</style>
"""

def apply_dark_theme():
    """Apply dark theme styles to the Streamlit app."""
    st.markdown(DARK_THEME_CSS, unsafe_allow_html=True) 