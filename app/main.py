"""
IPO Backtest Terminal UI
Modern finance-focused interface with dark theme
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, date, timedelta
import json
from pathlib import Path
import time
from backtest_engine import IPOBacktestEngine
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Page configuration
st.set_page_config(
    page_title="IPO Backtest Terminal",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for dark theme with sharp edges and Helvetica fonts
st.markdown("""
<style>
    /* Main container centering */
    .stApp > div:first-child {
        max-width: 1200px;
        margin: 0 auto;
        padding: 20px 40px;
    }

    /* Font family override - Body text */
    * {
        font-family: 'Helvetica Neue', 'Helvetica', sans-serif !important;
        font-weight: 400;
    }

    /* Bold headings and buttons - Helvetica Bold */
    h1, h2, h3, h4, h5, h6, .stButton > button, .main-header, .stMarkdown h3, .stMarkdown h4 {
        font-family: 'Helvetica Bold', 'Helvetica Neue', 'Helvetica', sans-serif !important;
        font-weight: 700;
    }

    /* Main background */
    .stApp {
        background-color: #0a0a0a;
        color: #ffffff;
    }

    /* Content spacing */
    .main-content {
        padding: 20px;
        margin: 20px 0;
    }

    /* Section spacing */
    .section-spacing {
        margin: 30px 0;
        padding: 0 20px;
    }

    /* Remove rounded corners */
    .stButton > button {
        background-color: transparent;
        border: 1px solid #ffffff;
        color: #ffffff;
        border-radius: 0px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        transition: all 0.2s;
    }

    .stButton > button:hover {
        background-color: #ffffff;
        color: #0a0a0a;
        box-shadow: 0 0 20px rgba(255,255,255,0.3);
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #1a1a1a;
        border-bottom: 2px solid #333333;
        justify-content: center;
        display: flex;
    }

    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        border-radius: 0px;
        color: #888888;
        border: none;
        font-weight: 600;
        letter-spacing: 1px;
        font-family: 'Helvetica Bold', 'Helvetica Neue', 'Helvetica', sans-serif !important;
    }

    .stTabs [aria-selected="true"] {
        background-color: transparent;
        color: #ffffff;
        border-bottom: 2px solid #ffffff;
    }

    /* Input fields */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stDateInput > div > div > input,
    .stSelectbox > div > div > div {
        background-color: #1a1a1a;
        color: #ffffff;
        border: 1px solid #333333;
        border-radius: 0px;
    }

    /* Dropdown menus - straight edges */
    .stSelectbox > div > div > div > div {
        border-radius: 0px !important;
        background-color: #1a1a1a !important;
        border: 1px solid #ffffff !important;
    }

    .stSelectbox [data-baseweb="select"] > div {
        border-radius: 0px !important;
        background-color: #1a1a1a !important;
        border: 1px solid #ffffff !important;
    }

    /* Slider styling */
    .stSlider > div > div > div {
        background-color: #333333;
    }

    .stSlider > div > div > div > div {
        background-color: #ffffff;
    }

    /* Metric cards */
    [data-testid="metric-container"] {
        background-color: #1a1a1a;
        border: 1px solid #333333;
        padding: 15px;
        border-radius: 0px;
    }

    /* Progress bar */
    .stProgress > div > div > div > div {
        background-color: #00ff88;
    }

    /* Success/Error messages */
    .stSuccess {
        background-color: rgba(0, 255, 136, 0.1);
        border: 1px solid #00ff88;
        border-radius: 0px;
    }

    .stError {
        background-color: rgba(255, 51, 102, 0.1);
        border: 1px solid #ff3366;
        border-radius: 0px;
    }

    /* Advanced Options Expander Fixes */
    .streamlit-expanderHeader {
        background-color: #1a1a1a !important;
        border: 1px solid #333333 !important;
        border-radius: 0px !important;
        color: #ffffff !important;
        font-family: 'Helvetica Bold', 'Helvetica Neue', 'Helvetica', sans-serif !important;
        font-weight: 700 !important;
    }

    /* Hide the default expander arrow text */
    .streamlit-expanderHeader svg {
        color: #ffffff !important;
    }

    /* Fix expander content styling */
    .streamlit-expanderContent {
        background-color: #0a0a0a !important;
        border: 1px solid #333333 !important;
        border-top: none !important;
        border-radius: 0px !important;
    }

    /* Fix expander text artifacts - More aggressive approach */
    .streamlit-expanderHeader div div div {
        font-size: 0 !important;
    }

    .streamlit-expanderHeader div div div span {
        font-size: 14px !important;
        font-family: 'Helvetica Bold', 'Helvetica Neue', 'Helvetica', sans-serif !important;
        font-weight: 700 !important;
    }

    /* Hide specific text nodes containing keyboard_arrow_down */
    .streamlit-expanderHeader * {
        text-indent: -9999px;
        line-height: 0;
    }

    .streamlit-expanderHeader svg {
        text-indent: 0 !important;
        line-height: normal !important;
    }

    .streamlit-expanderHeader span:first-child {
        text-indent: 0 !important;
        line-height: normal !important;
    }

    /* Alternative approach - hide all text except the label */
    [data-testid="stExpander"] summary div div:not(:first-child) {
        display: none !important;
    }

    /* Custom config summary box */
    .config-summary {
        background-color: #0a0a0a;
        border: 1px solid #ffffff;
        padding: 20px;
        border-radius: 0px;
        margin: 20px 0;
        font-family: 'Helvetica Neue', 'Helvetica', sans-serif !important;
    }

    /* Checkbox styling fix */
    .stCheckbox > label > div[data-testid="stCheckbox"] > div {
        background-color: #1a1a1a !important;
        border: 1px solid #ffffff !important;
        border-radius: 0px !important;
    }

    .stCheckbox > label > div[data-testid="stCheckbox"] > div[data-checked="true"] {
        background-color: #ffffff !important;
    }

    .stCheckbox > label > div[data-testid="stCheckbox"] > div[data-checked="true"] svg {
        color: #0a0a0a !important;
    }

    /* Data source info button */
    .info-button {
        width: 30px !important;
        height: 30px !important;
        min-height: 30px !important;
        padding: 0 !important;
        font-size: 14px !important;
    }

    /* Custom header */
    .main-header {
        font-size: 2.5em;
        font-weight: 700;
        font-family: 'Helvetica Bold', 'Helvetica Neue', 'Helvetica', sans-serif !important;
        text-transform: uppercase;
        letter-spacing: 3px;
        border-bottom: 1px solid #333333;
        padding-bottom: 20px;
        margin-bottom: 30px;
        text-align: center;
    }

    /* Custom card */
    .result-card {
        background-color: #1a1a1a;
        border: 1px solid #333333;
        padding: 20px;
        margin: 10px 0;
        transition: all 0.3s;
    }

    .result-card:hover {
        border-color: #ffffff;
        box-shadow: 0 0 15px rgba(255,255,255,0.1);
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>

<script>
// JavaScript solution to remove keyboard_arrow_down text
document.addEventListener('DOMContentLoaded', function() {
    function removeKeyboardArrowText() {
        const expanderHeaders = document.querySelectorAll('[data-testid="stExpander"] summary');
        expanderHeaders.forEach(header => {
            const walker = document.createTreeWalker(
                header,
                NodeFilter.SHOW_TEXT,
                null,
                false
            );

            const textNodes = [];
            let node;
            while (node = walker.nextNode()) {
                textNodes.push(node);
            }

            textNodes.forEach(textNode => {
                if (textNode.textContent.includes('keyboard_arrow_down')) {
                    textNode.textContent = textNode.textContent.replace(/keyboard_arrow_down/g, '');
                }
            });
        });
    }

    // Run immediately and on mutations
    removeKeyboardArrowText();

    const observer = new MutationObserver(removeKeyboardArrowText);
    observer.observe(document.body, { childList: true, subtree: true });
});
</script>
""", unsafe_allow_html=True)

# Initialize session state
if 'running_backtest' not in st.session_state:
    st.session_state.running_backtest = False
if 'backtest_results' not in st.session_state:
    st.session_state.backtest_results = None

# Header
st.markdown('<div class="main-header">IPO BACKTEST TERMINAL</div>', unsafe_allow_html=True)

# Main tabs
tab1, tab2, tab3 = st.tabs(["NEW BACKTEST", "GALLERY", "ANALYTICS"])

# Tab 1: New Backtest
with tab1:
    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("### CONFIGURATION")
        st.markdown("---")

        # Training split slider
        train_split = st.slider(
            "Training Split",
            min_value=50,
            max_value=90,
            value=70,
            step=5,
            format="%d%%",
            help="Percentage of data used for training"
        )
        test_split = 100 - train_split
        st.caption(f"Training: {train_split}% | Testing: {test_split}%")

        # Date range
        st.markdown("#### Date Range")
        start_date = st.date_input(
            "Start Date",
            value=date(2000, 1, 1),
            min_value=date(1990, 1, 1),
            max_value=date(2024, 12, 31)
        )

        end_date = st.date_input(
            "End Date",
            value=date.today(),
            min_value=start_date,
            max_value=date(2025, 12, 31)
        )

        # Advanced options
        with st.expander("ADVANCED OPTIONS"):
            initial_capital = st.number_input(
                "Initial Capital ($)",
                min_value=10000,
                max_value=10000000,
                value=100000,
                step=10000
            )

            # Data source with tooltip
            data_mode = st.radio(
                "Data Source",
                ["SIMULATION", "YAHOO", "IBKR"],
                index=0,
                horizontal=True,
                help="""
                **SIMULATION**: Generated realistic data for testing and development

                **YAHOO**: Yahoo Finance historical data (limited to recent IPOs)

                **IBKR**: Interactive Brokers live data (requires TWS/Gateway connection)
                """
            )

            position_size = st.number_input(
                "Position Size (%)",
                min_value=1,
                max_value=10,
                value=2,
                step=1
            )

            cache_data = st.checkbox("Use Cached Data", value=True)

    with col2:
        st.markdown("### EXECUTION")
        st.markdown("---")

        # Configuration summary with custom styling
        st.markdown(f"""
        <div class="config-summary">
            <strong style="font-family: 'Helvetica Bold', sans-serif;">Configuration Summary:</strong><br>
            • Training: {train_split}%<br>
            • Testing: {test_split}%<br>
            • Period: {start_date} to {end_date}<br>
            • Capital: ${initial_capital:,}<br>
            • Data: {data_mode}
        </div>
        """, unsafe_allow_html=True)

        # Run button
        if st.button("RUN BACKTEST", use_container_width=True, disabled=st.session_state.running_backtest):
            st.session_state.running_backtest = True

            # Create config
            config = {
                'START_DATE': str(start_date),
                'END_DATE': str(end_date),
                'INITIAL_CAPITAL': initial_capital,
                'DATA_MODE': data_mode,
                'TRAIN_TEST_SPLIT': train_split / 100,
                'POSITION_SIZE': position_size / 100,
                'CACHE_DATA': cache_data,
                'USE_ALL_TICKERS': True,
                'GENERATE_PDF': True
            }

            # Progress container
            progress_bar = st.progress(0)
            status_text = st.empty()

            def update_progress(progress, message):
                progress_bar.progress(progress)
                status_text.text(message)

            # Run backtest
            try:
                engine = IPOBacktestEngine(config)
                results = engine.run_backtest(update_progress)
                st.session_state.backtest_results = results
                st.session_state.running_backtest = False

                # Success message
                st.success("Backtest Complete!")

                # Display results
                st.markdown("### RESULTS")
                st.markdown("---")

                # Optimal Strategy Section
                st.markdown("#### 🎯 OPTIMAL STRATEGY")
                st.markdown(f"""
                <div class="result-card">
                    <h4 style="color: #00ff88; margin-bottom: 10px;">{results['optimal_strategy']['window']}</h4>
                    <p><strong>Average Return:</strong> {results['optimal_strategy']['avg_return']:.2f}% per trade</p>
                    <p><strong>Win Rate:</strong> {results['optimal_strategy']['win_rate']:.1f}%</p>
                    <p><strong>Sharpe Ratio:</strong> {results['optimal_strategy']['sharpe']:.2f}</p>
                    <p><strong>Duration:</strong> {results['optimal_strategy']['duration_hrs']:.1f} hours</p>
                </div>
                """, unsafe_allow_html=True)
                st.markdown("---")

                # Training Results Section
                st.markdown("#### 📊 TRAINING SET PERFORMANCE")
                st.markdown(f"""
                <div class="result-card">
                    <p><strong>Final Value:</strong> ${results['train_portfolio']['final_value']:,.2f}</p>
                    <p><strong>Total Return:</strong> {results['train_portfolio']['total_return_pct']:+.2f}%</p>
                    <p><strong>CAGR:</strong> {results['train_portfolio']['cagr']:.2f}%</p>
                    <p><strong>Total Trades:</strong> {results['train_portfolio'].get('total_trades', 'N/A')}</p>
                    <p><strong>Win Rate:</strong> {results['train_portfolio'].get('win_rate', 'N/A'):.1f}%</p>
                </div>
                """, unsafe_allow_html=True)
                st.markdown("---")

                # Test Results Section
                st.markdown("#### 🧪 TEST SET PERFORMANCE (Out-of-Sample)")
                st.markdown(f"""
                <div class="result-card">
                    <p><strong>Final Value:</strong> ${results['test_portfolio']['final_value']:,.2f}</p>
                    <p><strong>Total Return:</strong> {results['test_portfolio']['total_return_pct']:+.2f}%</p>
                    <p><strong>CAGR:</strong> {results['test_portfolio']['cagr']:.2f}%</p>
                    <p><strong>Total Trades:</strong> {results['test_portfolio'].get('total_trades', 'N/A')}</p>
                    <p><strong>Win Rate:</strong> {results['test_portfolio'].get('win_rate', 'N/A'):.1f}%</p>
                </div>
                """, unsafe_allow_html=True)
                st.markdown("---")

                # Strategy Degradation Analysis
                st.markdown("#### 📉 STRATEGY VALIDATION")
                degradation = ((results['test_portfolio']['total_return_pct'] /
                              results['train_portfolio']['total_return_pct']) - 1) * 100 if \
                              results['train_portfolio']['total_return_pct'] != 0 else 0

                degradation_color = "#00ff88" if abs(degradation) < 30 else "#ff3366"
                degradation_status = "Robust Strategy" if abs(degradation) < 30 else "Potential Overfitting"

                st.markdown(f"""
                <div class="result-card">
                    <p><strong>Performance Degradation:</strong> <span style="color: {degradation_color};">{degradation:.1f}%</span></p>
                    <p><strong>Strategy Status:</strong> <span style="color: {degradation_color};">{degradation_status}</span></p>
                    <p><strong>Validation:</strong> {"✅ Strategy generalizes well to unseen data" if abs(degradation) < 30 else "⚠️ Strategy may be overfit to training data"}</p>
                </div>
                """, unsafe_allow_html=True)
                st.markdown("---")

                # Benchmark Comparison Section
                st.markdown("#### 📈 BENCHMARK COMPARISON")
                spy_data = results['spy_benchmark']
                outperformance = results['test_portfolio']['total_return_pct'] - spy_data['total_return_pct']
                outperformance_color = "#00ff88" if outperformance > 0 else "#ff3366"

                st.markdown(f"""
                <div class="result-card">
                    <h5 style="margin-bottom: 15px;">IPO Strategy vs SPY Buy & Hold</h5>
                    <p><strong>IPO Strategy (Test):</strong> {results['test_portfolio']['total_return_pct']:+.2f}% (${results['test_portfolio']['final_value']:,.0f})</p>
                    <p><strong>SPY Buy & Hold:</strong> {spy_data['total_return_pct']:+.2f}% (${spy_data['final_value']:,.0f})</p>
                    <p><strong>Outperformance:</strong> <span style="color: {outperformance_color};">{outperformance:+.2f}%</span></p>
                    <p><strong>Result:</strong> <span style="color: {outperformance_color};">{"🎉 Beats SPY" if outperformance > 0 else "📉 Underperforms SPY"}</span></p>
                </div>
                """, unsafe_allow_html=True)

                # Save results path
                st.info(f"Results saved to: {results['output_dir']}")

            except Exception as e:
                st.error(f"Backtest failed: {str(e)}")
                st.session_state.running_backtest = False

# Tab 2: Gallery
with tab2:
    st.markdown("### BACKTEST HISTORY")
    st.markdown("---")

    # Filter controls
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        filter_option = st.selectbox("Filter", ["All", "Last 7 Days", "Last 30 Days", "Custom"])
    with col2:
        sort_option = st.selectbox("Sort By", ["Date (Newest)", "Date (Oldest)", "Return (High)", "Return (Low)"])
    with col3:
        if st.button("REFRESH", use_container_width=True):
            st.rerun()

    # Load existing backtests
    outputs_dir = Path("outputs")
    if outputs_dir.exists():
        backtest_dirs = [d for d in outputs_dir.iterdir() if d.is_dir() and d.name.startswith("backtest_")]

        # Load all backtest data for filtering and sorting
        backtest_data = []
        for backtest_dir in backtest_dirs:
            results_file = backtest_dir / "analysis" / "backtest_results.json"
            if results_file.exists():
                try:
                    with open(results_file, 'r') as f:
                        results = json.load(f)

                    # Parse folder name for date/time
                    folder_parts = backtest_dir.name.split('_')
                    if len(folder_parts) >= 3:
                        run_date = folder_parts[1]
                        run_time = folder_parts[2]

                        # Convert to datetime for filtering
                        try:
                            run_datetime = datetime.strptime(f"{run_date} {run_time}", "%Y-%m-%d %H%M%S")
                        except:
                            run_datetime = datetime.now()

                        backtest_data.append({
                            'dir': backtest_dir,
                            'datetime': run_datetime,
                            'date': run_date,
                            'time': run_time,
                            'results': results
                        })
                except:
                    continue

        # Apply filtering
        filtered_data = backtest_data.copy()
        if filter_option == "Last 7 Days":
            cutoff_date = datetime.now() - timedelta(days=7)
            filtered_data = [d for d in filtered_data if d['datetime'] >= cutoff_date]
        elif filter_option == "Last 30 Days":
            cutoff_date = datetime.now() - timedelta(days=30)
            filtered_data = [d for d in filtered_data if d['datetime'] >= cutoff_date]

        # Apply sorting
        if sort_option == "Date (Newest)":
            filtered_data.sort(key=lambda x: x['datetime'], reverse=True)
        elif sort_option == "Date (Oldest)":
            filtered_data.sort(key=lambda x: x['datetime'])
        elif sort_option == "Return (High)":
            filtered_data.sort(key=lambda x: x['results']['test_portfolio'].get('total_return_pct', 0), reverse=True)
        elif sort_option == "Return (Low)":
            filtered_data.sort(key=lambda x: x['results']['test_portfolio'].get('total_return_pct', 0))

        # Display results
        if filtered_data:
            for data in filtered_data[:20]:  # Show up to 20 results
                backtest_dir = data['dir']
                results = data['results']
                run_date = data['date']
                run_time = data['time']

                # Create result card
                with st.container():
                    st.markdown(f"""
                    <div class="result-card">
                        <h4 style="color: #00ff88; margin-bottom: 10px;">{run_date} {run_time[:2]}:{run_time[2:4]}:{run_time[4:]}</h4>
                        <p><strong>Strategy:</strong> {results['optimal_strategy']['window']}</p>
                        <p><strong>Training Return:</strong> {results['train_portfolio']['total_return_pct']:.2f}%</p>
                        <p><strong>Test Return:</strong> {results['test_portfolio']['total_return_pct']:.2f}%</p>
                        <p><strong>Win Rate:</strong> {results['train_portfolio'].get('win_rate', 0):.1f}%</p>
                    </div>
                    """, unsafe_allow_html=True)

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button(f"VIEW DETAILS", key=f"view_{backtest_dir.name}"):
                            # Show detailed results in expander
                            with st.expander("📊 Detailed Results", expanded=True):
                                detail_col1, detail_col2 = st.columns(2)

                                with detail_col1:
                                    st.markdown("**Training Set:**")
                                    st.write(f"• Final Value: ${results['train_portfolio']['final_value']:,.2f}")
                                    st.write(f"• CAGR: {results['train_portfolio']['cagr']:.2f}%")
                                    st.write(f"• Total Trades: {results['train_portfolio'].get('total_trades', 'N/A')}")

                                with detail_col2:
                                    st.markdown("**Test Set:**")
                                    st.write(f"• Final Value: ${results['test_portfolio']['final_value']:,.2f}")
                                    st.write(f"• CAGR: {results['test_portfolio']['cagr']:.2f}%")
                                    st.write(f"• Total Trades: {results['test_portfolio'].get('total_trades', 'N/A')}")

                                st.markdown("**Configuration:**")
                                st.write(f"• Period: {results.get('split_info', {}).get('train_start', 'N/A')} to {results.get('split_info', {}).get('test_end', 'N/A')}")
                                st.write(f"• Strategy: {results['optimal_strategy']['window']}")

                    with col2:
                        pdf_path = backtest_dir / "reports" / "IPO_Strategy_Complete_Report.pdf"
                        if pdf_path.exists():
                            with open(pdf_path, "rb") as pdf:
                                st.download_button(
                                    "DOWNLOAD PDF",
                                    pdf.read(),
                                    file_name=f"ipo_report_{run_date}_{run_time}.pdf",
                                    mime="application/pdf",
                                    key=f"pdf_{backtest_dir.name}"
                                )
                        else:
                            st.button("PDF N/A", disabled=True, key=f"no_pdf_{backtest_dir.name}")

                    with col3:
                        if st.button(f"DELETE", type="secondary", key=f"del_{backtest_dir.name}"):
                            # Add confirmation in session state
                            st.session_state[f"confirm_delete_{backtest_dir.name}"] = True

                        # Show confirmation if delete was clicked
                        if st.session_state.get(f"confirm_delete_{backtest_dir.name}", False):
                            if st.button(f"✅ CONFIRM DELETE", type="primary", key=f"confirm_del_{backtest_dir.name}"):
                                import shutil
                                try:
                                    shutil.rmtree(backtest_dir)
                                    st.success(f"Deleted backtest from {run_date}")
                                    # Clean up session state
                                    del st.session_state[f"confirm_delete_{backtest_dir.name}"]
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error deleting: {str(e)}")
                    st.markdown("---")
        else:
            st.info(f"No backtests found for filter: {filter_option}")
    else:
        st.info("No backtests found. Run a new backtest to see results here.")

# Tab 3: Analytics
with tab3:
    st.markdown("### PERFORMANCE ANALYTICS")
    st.markdown("---")

    # Load all results for analytics
    if outputs_dir.exists():
        all_results = []
        for backtest_dir in outputs_dir.iterdir():
            if backtest_dir.is_dir() and backtest_dir.name.startswith("backtest_"):
                results_file = backtest_dir / "analysis" / "backtest_results.json"
                if results_file.exists():
                    with open(results_file, 'r') as f:
                        result = json.load(f)
                        result['date'] = backtest_dir.name.split('_')[1]
                        all_results.append(result)

        if all_results:
            # Create DataFrame
            df = pd.DataFrame([{
                'Date': r['date'],
                'Strategy': r['optimal_strategy']['window'],
                'Train Return': r['train_portfolio']['total_return_pct'],
                'Test Return': r['test_portfolio']['total_return_pct'],
                'Win Rate': r['train_portfolio']['win_rate']
            } for r in all_results])

            # Performance over time chart - Fixed to show complete timeline
            st.markdown("#### 📈 PERFORMANCE OVER TIME")
            fig = go.Figure()

            # Sort by date to ensure proper timeline
            df_sorted = df.sort_values('Date')

            fig.add_trace(go.Scatter(
                x=df_sorted['Date'],
                y=df_sorted['Train Return'],
                mode='lines+markers',
                name='Training Return',
                line=dict(color='#00ff88', width=3),
                marker=dict(size=6)
            ))
            fig.add_trace(go.Scatter(
                x=df_sorted['Date'],
                y=df_sorted['Test Return'],
                mode='lines+markers',
                name='Test Return',
                line=dict(color='#ff3366', width=3),
                marker=dict(size=6)
            ))
            fig.update_layout(
                title=dict(text="", font=dict(size=16)),
                xaxis_title="Date",
                yaxis_title="Return (%)",
                plot_bgcolor='#0a0a0a',
                paper_bgcolor='#0a0a0a',
                font=dict(color='white', family='Helvetica Neue'),
                showlegend=True,
                hovermode='x unified',
                height=400,
                legend=dict(
                    yanchor="top",
                    y=0.99,
                    xanchor="left",
                    x=0.01
                )
            )
            fig.update_xaxes(
                gridcolor='#333333',
                showgrid=True,
                type='category'  # Treat dates as categories to show all points
            )
            fig.update_yaxes(gridcolor='#333333', showgrid=True)

            st.plotly_chart(fig, use_container_width=True)
            st.markdown("---")

            # Most Common Strategies - Vertical Layout
            st.markdown("#### 🎯 MOST COMMON STRATEGIES")
            strategy_counts = df['Strategy'].value_counts().head(10)  # Show top 10
            fig2 = go.Figure(data=[
                go.Bar(
                    x=strategy_counts.index,
                    y=strategy_counts.values,
                    marker=dict(color='#00ff88', line=dict(color='#ffffff', width=1)),
                    text=strategy_counts.values,
                    textposition='auto'
                )
            ])
            fig2.update_layout(
                title=dict(text="", font=dict(size=16)),
                xaxis_title="Trading Strategy",
                yaxis_title="Frequency",
                plot_bgcolor='#0a0a0a',
                paper_bgcolor='#0a0a0a',
                font=dict(color='white', family='Helvetica Neue'),
                height=400,
                xaxis=dict(tickangle=45)
            )
            fig2.update_xaxes(gridcolor='#333333', showgrid=True)
            fig2.update_yaxes(gridcolor='#333333', showgrid=True)
            st.plotly_chart(fig2, use_container_width=True)
            st.markdown("---")

            # Win Rate Distribution - Full Width
            st.markdown("#### 🏆 WIN RATE DISTRIBUTION")
            fig3 = go.Figure(data=[
                go.Histogram(
                    x=df['Win Rate'],
                    nbinsx=20,
                    marker=dict(color='#ff3366', opacity=0.7, line=dict(color='#ffffff', width=1)),
                    name="Win Rate"
                )
            ])
            fig3.update_layout(
                title=dict(text="", font=dict(size=16)),
                xaxis_title="Win Rate (%)",
                yaxis_title="Number of Backtests",
                plot_bgcolor='#0a0a0a',
                paper_bgcolor='#0a0a0a',
                font=dict(color='white', family='Helvetica Neue'),
                height=400,
                showlegend=False
            )
            fig3.update_xaxes(gridcolor='#333333', showgrid=True)
            fig3.update_yaxes(gridcolor='#333333', showgrid=True)
            st.plotly_chart(fig3, use_container_width=True)
            st.markdown("---")

            # SPY Benchmark Analysis
            st.markdown("#### 📊 SPY BENCHMARK COMPARISON")

            # Load SPY benchmark data from all backtests
            spy_data = []
            strategy_vs_spy = []

            for backtest_dir in outputs_dir.iterdir():
                if backtest_dir.is_dir() and backtest_dir.name.startswith("backtest_"):
                    results_file = backtest_dir / "analysis" / "backtest_results.json"
                    if results_file.exists():
                        try:
                            with open(results_file, 'r') as f:
                                result = json.load(f)

                            # Only include results that have SPY benchmark data
                            if 'spy_benchmark' in result:
                                spy_return = result['spy_benchmark']['total_return_pct']
                                test_return = result['test_portfolio']['total_return_pct']
                                outperformance = test_return - spy_return

                                spy_data.append(spy_return)
                                strategy_vs_spy.append({
                                    'Date': backtest_dir.name.split('_')[1],
                                    'Strategy Return': test_return,
                                    'SPY Return': spy_return,
                                    'Outperformance': outperformance,
                                    'Beats SPY': outperformance > 0
                                })
                        except:
                            continue

            if strategy_vs_spy:
                spy_df = pd.DataFrame(strategy_vs_spy)

                # SPY vs Strategy Performance Chart
                fig_spy = go.Figure()

                fig_spy.add_trace(go.Scatter(
                    x=spy_df['Date'],
                    y=spy_df['Strategy Return'],
                    mode='lines+markers',
                    name='IPO Strategy',
                    line=dict(color='#00ff88', width=3),
                    marker=dict(size=8)
                ))

                fig_spy.add_trace(go.Scatter(
                    x=spy_df['Date'],
                    y=spy_df['SPY Return'],
                    mode='lines+markers',
                    name='SPY Buy & Hold',
                    line=dict(color='#ff3366', width=3),
                    marker=dict(size=8)
                ))

                fig_spy.update_layout(
                    title=dict(text="", font=dict(size=16)),
                    xaxis_title="Backtest Date",
                    yaxis_title="Total Return (%)",
                    plot_bgcolor='#0a0a0a',
                    paper_bgcolor='#0a0a0a',
                    font=dict(color='white', family='Helvetica Neue'),
                    showlegend=True,
                    hovermode='x unified',
                    height=400,
                    legend=dict(
                        yanchor="top",
                        y=0.99,
                        xanchor="left",
                        x=0.01
                    )
                )
                fig_spy.update_xaxes(gridcolor='#333333', showgrid=True, type='category')
                fig_spy.update_yaxes(gridcolor='#333333', showgrid=True)

                st.plotly_chart(fig_spy, use_container_width=True)
                st.markdown("---")

                # Outperformance Distribution
                st.markdown("#### 🎯 OUTPERFORMANCE DISTRIBUTION")
                fig_outperf = go.Figure(data=[
                    go.Histogram(
                        x=spy_df['Outperformance'],
                        nbinsx=15,
                        marker=dict(
                            color=['#00ff88' if x > 0 else '#ff3366' for x in spy_df['Outperformance']],
                            opacity=0.7,
                            line=dict(color='#ffffff', width=1)
                        ),
                        name="Outperformance"
                    )
                ])
                fig_outperf.update_layout(
                    title=dict(text="", font=dict(size=16)),
                    xaxis_title="Outperformance vs SPY (%)",
                    yaxis_title="Number of Backtests",
                    plot_bgcolor='#0a0a0a',
                    paper_bgcolor='#0a0a0a',
                    font=dict(color='white', family='Helvetica Neue'),
                    height=400,
                    showlegend=False
                )
                fig_outperf.update_xaxes(gridcolor='#333333', showgrid=True)
                fig_outperf.update_yaxes(gridcolor='#333333', showgrid=True)

                # Add vertical line at zero
                fig_outperf.add_vline(x=0, line_dash="dash", line_color="white", opacity=0.7)

                st.plotly_chart(fig_outperf, use_container_width=True)
                st.markdown("---")

                # SPY Comparison Statistics
                st.markdown("#### 🏆 SPY BENCHMARK STATISTICS")
                beats_spy_count = sum(spy_df['Beats SPY'])
                total_backtests = len(spy_df)
                win_rate_vs_spy = (beats_spy_count / total_backtests) * 100
                avg_outperformance = spy_df['Outperformance'].mean()

                spy_col1, spy_col2, spy_col3, spy_col4 = st.columns(4)

                with spy_col1:
                    st.metric(
                        "Win Rate vs SPY",
                        f"{win_rate_vs_spy:.1f}%",
                        f"{beats_spy_count}/{total_backtests} wins"
                    )

                with spy_col2:
                    st.metric(
                        "Avg Outperformance",
                        f"{avg_outperformance:+.2f}%",
                        "Beats SPY" if avg_outperformance > 0 else "Underperforms"
                    )

                with spy_col3:
                    st.metric(
                        "Best Outperformance",
                        f"{spy_df['Outperformance'].max():+.2f}%"
                    )

                with spy_col4:
                    st.metric(
                        "Worst Outperformance",
                        f"{spy_df['Outperformance'].min():+.2f}%"
                    )

                st.markdown("---")
            else:
                st.info("📊 No SPY benchmark data available. Run new backtests to see SPY comparison analytics.")

            # Summary statistics
            st.markdown("#### 📈 SUMMARY STATISTICS")
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Average Train Return", f"{df['Train Return'].mean():.2f}%")
            with col2:
                st.metric("Average Test Return", f"{df['Test Return'].mean():.2f}%")
            with col3:
                st.metric("Best Strategy", df.loc[df['Test Return'].idxmax(), 'Strategy'])
            with col4:
                st.metric("Average Win Rate", f"{df['Win Rate'].mean():.1f}%")
        else:
            st.info("No backtest data available for analytics.")
    else:
        st.info("No backtest data available for analytics.")