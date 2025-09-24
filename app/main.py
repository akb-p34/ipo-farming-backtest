"""
IPO Backtest Terminal UI
Modern finance-focused interface with dark theme
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, date
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
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for dark theme with sharp edges
st.markdown("""
<style>
    /* Main background */
    .stApp {
        background-color: #0a0a0a;
        color: #ffffff;
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
    }

    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        border-radius: 0px;
        color: #888888;
        border: none;
        font-weight: 600;
        letter-spacing: 1px;
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

    /* Custom header */
    .main-header {
        font-size: 2.5em;
        font-weight: 100;
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
""", unsafe_allow_html=True)

# Initialize session state
if 'running_backtest' not in st.session_state:
    st.session_state.running_backtest = False
if 'backtest_results' not in st.session_state:
    st.session_state.backtest_results = None

# Header
st.markdown('<div class="main-header">IPO BACKTEST TERMINAL</div>', unsafe_allow_html=True)

# Main tabs
tab1, tab2, tab3 = st.tabs(["📊 NEW BACKTEST", "📁 GALLERY", "📈 ANALYTICS"])

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
            value=date(2025, 9, 30),
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

            data_mode = st.radio(
                "Data Source",
                ["SIMULATION", "YAHOO", "IBKR"],
                index=0,
                horizontal=True
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

        # Quick stats
        st.info(f"""
        **Configuration Summary:**
        - Training: {train_split}%
        - Testing: {test_split}%
        - Period: {start_date} to {end_date}
        - Capital: ${initial_capital:,}
        - Data: {data_mode}
        """)

        # Run button
        if st.button("▶ RUN BACKTEST", use_container_width=True, disabled=st.session_state.running_backtest):
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
                st.success("✅ Backtest Complete!")

                # Display results
                st.markdown("### RESULTS")

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric(
                        "Optimal Strategy",
                        results['optimal_strategy']['window'],
                        f"{results['optimal_strategy']['avg_return']:.2f}%"
                    )

                with col2:
                    st.metric(
                        "Training Return",
                        f"{results['train_portfolio']['total_return_pct']:.2f}%",
                        f"CAGR: {results['train_portfolio']['cagr']:.2f}%"
                    )

                with col3:
                    st.metric(
                        "Test Return",
                        f"{results['test_portfolio']['total_return_pct']:.2f}%",
                        f"CAGR: {results['test_portfolio']['cagr']:.2f}%"
                    )

                with col4:
                    degradation = ((results['test_portfolio']['total_return_pct'] /
                                  results['train_portfolio']['total_return_pct']) - 1) * 100 if \
                                  results['train_portfolio']['total_return_pct'] != 0 else 0

                    st.metric(
                        "Degradation",
                        f"{degradation:.1f}%",
                        "✅ Robust" if abs(degradation) < 30 else "⚠️ Overfitting"
                    )

                # Save results path
                st.info(f"📁 Results saved to: {results['output_dir']}")

            except Exception as e:
                st.error(f"❌ Backtest failed: {str(e)}")
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
        if st.button("🔄 REFRESH"):
            st.rerun()

    # Load existing backtests
    outputs_dir = Path("outputs")
    if outputs_dir.exists():
        backtest_dirs = sorted([d for d in outputs_dir.iterdir() if d.is_dir() and d.name.startswith("backtest_")],
                              reverse=True)

        # Display results
        for backtest_dir in backtest_dirs[:10]:  # Show last 10
            # Try to load results
            results_file = backtest_dir / "analysis" / "backtest_results.json"
            config_file = backtest_dir / "data" / "config.json"

            if results_file.exists():
                with open(results_file, 'r') as f:
                    results = json.load(f)

                # Parse folder name for date/time
                folder_parts = backtest_dir.name.split('_')
                if len(folder_parts) >= 3:
                    run_date = folder_parts[1]
                    run_time = folder_parts[2]

                    # Create result card
                    with st.container():
                        st.markdown(f"""
                        <div class="result-card">
                            <h4>📊 {run_date} {run_time[:2]}:{run_time[2:4]}:{run_time[4:]}</h4>
                            <p><b>Strategy:</b> {results['optimal_strategy']['window']}</p>
                            <p><b>Training Return:</b> {results['train_portfolio']['total_return_pct']:.2f}%</p>
                            <p><b>Test Return:</b> {results['test_portfolio']['total_return_pct']:.2f}%</p>
                            <p><b>Win Rate:</b> {results['train_portfolio']['win_rate']:.1f}%</p>
                        </div>
                        """, unsafe_allow_html=True)

                        col1, col2, col3 = st.columns(3)
                        with col1:
                            if st.button(f"VIEW #{backtest_dir.name[-10:]}", key=f"view_{backtest_dir.name}"):
                                st.session_state.selected_backtest = backtest_dir
                        with col2:
                            pdf_path = backtest_dir / "reports" / "IPO_Strategy_Complete_Report.pdf"
                            if pdf_path.exists():
                                with open(pdf_path, "rb") as pdf:
                                    st.download_button(
                                        "DOWNLOAD PDF",
                                        pdf.read(),
                                        file_name=f"report_{run_date}_{run_time}.pdf",
                                        mime="application/pdf",
                                        key=f"pdf_{backtest_dir.name}"
                                    )
                        with col3:
                            if st.button(f"DELETE", key=f"del_{backtest_dir.name}"):
                                if st.button(f"CONFIRM DELETE", key=f"confirm_del_{backtest_dir.name}"):
                                    import shutil
                                    shutil.rmtree(backtest_dir)
                                    st.rerun()
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

            # Performance over time chart
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df['Date'],
                y=df['Train Return'],
                mode='lines+markers',
                name='Training Return',
                line=dict(color='#00ff88', width=2)
            ))
            fig.add_trace(go.Scatter(
                x=df['Date'],
                y=df['Test Return'],
                mode='lines+markers',
                name='Test Return',
                line=dict(color='#ff3366', width=2)
            ))
            fig.update_layout(
                title="Performance Over Time",
                xaxis_title="Date",
                yaxis_title="Return (%)",
                plot_bgcolor='#0a0a0a',
                paper_bgcolor='#0a0a0a',
                font=dict(color='white'),
                showlegend=True,
                hovermode='x unified'
            )
            fig.update_xaxes(gridcolor='#333333')
            fig.update_yaxes(gridcolor='#333333')

            st.plotly_chart(fig, use_container_width=True)

            # Strategy frequency
            col1, col2 = st.columns(2)

            with col1:
                strategy_counts = df['Strategy'].value_counts()
                fig2 = go.Figure(data=[
                    go.Bar(
                        x=strategy_counts.index,
                        y=strategy_counts.values,
                        marker=dict(color='#00ff88')
                    )
                ])
                fig2.update_layout(
                    title="Most Common Strategies",
                    xaxis_title="Strategy",
                    yaxis_title="Frequency",
                    plot_bgcolor='#0a0a0a',
                    paper_bgcolor='#0a0a0a',
                    font=dict(color='white')
                )
                fig2.update_xaxes(gridcolor='#333333')
                fig2.update_yaxes(gridcolor='#333333')
                st.plotly_chart(fig2, use_container_width=True)

            with col2:
                # Win rate distribution
                fig3 = go.Figure(data=[
                    go.Histogram(
                        x=df['Win Rate'],
                        nbinsx=20,
                        marker=dict(color='#ff3366')
                    )
                ])
                fig3.update_layout(
                    title="Win Rate Distribution",
                    xaxis_title="Win Rate (%)",
                    yaxis_title="Frequency",
                    plot_bgcolor='#0a0a0a',
                    paper_bgcolor='#0a0a0a',
                    font=dict(color='white')
                )
                fig3.update_xaxes(gridcolor='#333333')
                fig3.update_yaxes(gridcolor='#333333')
                st.plotly_chart(fig3, use_container_width=True)

            # Summary statistics
            st.markdown("### SUMMARY STATISTICS")
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