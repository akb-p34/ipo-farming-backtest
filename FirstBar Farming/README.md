# FirstBar Farming - Professional Hedge Fund Analysis System

## 🏛️ Overview

FirstBar Farming is a professional-grade quantitative trading analysis system that implements and benchmarks the **First Bar Trading Strategy** with hedge fund-level metrics, reporting, and risk management.

### 📊 Key Features

- **🎯 Strategy Implementation**: Professional First Bar momentum trading system
- **📈 Multi-Asset Support**: Easy ticker switching (TQQQ, QQQ, SPY, etc.)
- **🏆 Comprehensive Benchmarking**: Against QQQ, TQQQ, and SPY buy-and-hold strategies
- **⚡ Advanced Analytics**: Sortino ratio, Sharpe ratio, Calmar ratio, maximum drawdown analysis
- **💰 Portfolio Simulation**: $100,000 cash analysis with realistic transaction costs and slippage
- **📊 Professional Visualizations**: Executive dashboards and performance comparisons
- **📄 Institutional Reporting**: Executive summaries, methodology documentation, and recommendations
- **🔌 IBKR Integration**: Live data from Interactive Brokers TWS API with automatic CSV export
- **💾 Data Transferability**: All market data automatically saved to CSV for backup and reuse

## 🎯 Strategy Logic

The FirstBar Strategy is based on momentum trading principles:

1. **Signal Generation**: Direction of first hourly trading bar determines trade direction
2. **Entry Timing**: Close of first trading hour (15:30 ET)
3. **Exit Conditions**: Profit target achievement OR end-of-day close
4. **Risk Management**: Same-day exits eliminate overnight gap risk
5. **Position Sizing**: Conservative 1% of portfolio per trade (configurable)

## 📁 Directory Structure

```
FirstBar Farming/
├── notebooks/           # Analysis notebooks
│   ├── FirstBar_Professional_Analysis.ipynb    # Main professional analysis
│   └── First_Bar_Strategy_Multi_Ticker.ipynb   # Original multi-ticker system
├── data/               # Raw market data (automatically saved CSV files from IBKR)
├── results/            # Strategy outputs, trades, and performance metrics
├── reports/            # Professional PDF reports and summaries
├── docs/              # Strategy documentation and guides
│   ├── QQQ_FirstBar_Strategy.md
│   └── TQQQ_FirstBar_Strategy_Guide.md
└── README.md          # This file
```

## 🚀 Quick Start

### Prerequisites

1. **Interactive Brokers Account** with TWS or IB Gateway
2. **Python Environment** with required packages:
   ```bash
   pip install pandas numpy matplotlib seaborn scipy ib_insync nest_asyncio
   ```
3. **Market Data Subscriptions** for desired assets

### Setup Instructions

1. **Launch TWS/IB Gateway** with API connections enabled
2. **Open Professional Notebook**: `notebooks/FirstBar_Professional_Analysis.ipynb`
3. **Configure Settings** in the configuration section:
   ```python
   STRATEGY_TICKER = "TQQQ"        # Primary ticker
   BENCHMARK_TICKERS = ["QQQ", "TQQQ", "SPY"]
   INITIAL_CAPITAL = 100000        # $100,000 starting capital
   POSITION_SIZE_PCT = 1.0         # 1% position sizing
   PROFIT_TARGET = 2.2             # 2.2% profit target
   ```
4. **Run All Cells** to execute comprehensive analysis

### Expected Output

- **Professional Dashboard**: Multi-panel visualization with performance comparisons
- **Executive Summary**: Hedge fund-grade performance metrics and rankings
- **Benchmark Analysis**: Comparison against buy-and-hold strategies
- **Risk Analytics**: Sharpe, Sortino, Calmar ratios with drawdown analysis
- **Trade Analysis**: Detailed trade-by-trade breakdown with statistics
- **Professional Reports**: Text-based executive reports and summaries

## 📊 Performance Metrics

The system calculates comprehensive performance metrics:

### Return Metrics
- Total Return (%)
- Annualized Return
- Compound Annual Growth Rate (CAGR)

### Risk Metrics
- **Sharpe Ratio**: Risk-adjusted return vs volatility
- **Sortino Ratio**: Risk-adjusted return vs downside deviation
- **Calmar Ratio**: Annual return vs maximum drawdown
- **Maximum Drawdown**: Largest peak-to-trough decline
- **Volatility**: Annualized standard deviation of returns

### Trade Statistics
- Total Number of Trades
- Win Rate (% of profitable trades)
- Profit Factor (Gross profit / Gross loss)
- Average Win/Loss amounts
- Largest Win/Loss trades

## 🎯 Configuration Options

### Strategy Parameters
- **STRATEGY_TICKER**: Primary asset for strategy testing
- **STRATEGY_MODE**: "buy", "sell", or "both" trade directions
- **PROFIT_TARGET**: Exit profit target percentage
- **SMA_FILTER**: Optional SMA filter period (0 = disabled)

### Portfolio Settings
- **INITIAL_CAPITAL**: Starting portfolio value
- **POSITION_SIZE_PCT**: Position size as percentage of portfolio
- **TRANSACTION_COST_PER_SHARE**: Realistic transaction costs
- **SLIPPAGE_BPS**: Market impact in basis points

### Data Settings
- **DATA_PERIOD**: Historical analysis period ("1 Y", "2 Y", "3 Y", etc.)
- **TWS_PORT**: IBKR connection port (7497=Paper, 7496=Live)
- **BENCHMARK_TICKERS**: List of comparison assets

## 📈 Sample Results

Based on historical analysis, the FirstBar Strategy has demonstrated:

- **Total Returns**: Competitive with buy-and-hold benchmarks
- **Risk-Adjusted Performance**: Superior Sharpe/Sortino ratios in many periods
- **Drawdown Control**: Limited maximum drawdowns compared to leveraged alternatives
- **Consistency**: Profitable across multiple market regimes

## ⚠️ Risk Management

### Built-in Risk Controls
- **Same-Day Exits**: Eliminates overnight gap risk
- **Position Sizing**: Conservative 1% allocation per trade
- **Profit Targets**: Systematic profit-taking mechanism
- **Transaction Costs**: Realistic cost modeling

### Recommended Additional Controls
- **Daily Loss Limits**: Maximum daily portfolio loss threshold
- **Drawdown Limits**: Strategy shutdown if maximum drawdown exceeded
- **Position Scaling**: Reduce size during high volatility periods
- **Regular Review**: Monthly performance and parameter assessment

## 🔧 Troubleshooting

### Common Issues

**IBKR Connection Problems:**
1. Ensure TWS/IB Gateway is running
2. Verify API connections are enabled (Configure → API → Settings)
3. Check correct port number (7497 for paper, 7496 for live)
4. Confirm market data subscriptions are active

**Data Quality Issues:**
1. Verify ticker symbols are correct
2. Check market data permissions for specific assets
3. Ensure sufficient historical data availability

**Performance Issues:**
1. Review parameter settings vs historical optimal values
2. Check for data gaps or missing bars
3. Validate trade logic for specific asset characteristics

## 📚 Documentation

- **Strategy Guide**: `docs/QQQ_FirstBar_Strategy.md` - Detailed strategy methodology
- **TQQQ Implementation**: `docs/TQQQ_FirstBar_Strategy_Guide.md` - Leveraged ETF considerations
- **Code Documentation**: Comprehensive inline documentation in notebooks

## ⚖️ Disclaimers

**Important Risk Warnings:**
- This system is for educational and research purposes only
- Past performance does not guarantee future results
- All trading involves substantial risk of loss
- Leveraged ETFs carry additional risks and complexity
- Consider paper trading extensively before live implementation

**Professional Advice:**
- Consult with qualified financial advisors
- Understand tax implications of active trading
- Ensure strategy fits within overall risk tolerance and investment objectives
- Comply with all applicable regulations and requirements

## 🤝 Contributing

This is a professional analysis system developed for educational and research purposes. Contributions should focus on:

- **Enhanced Analytics**: Additional performance metrics and risk measures
- **Improved Visualizations**: Professional charting and reporting enhancements
- **Extended Asset Coverage**: Support for additional asset classes
- **Risk Management**: Advanced risk control mechanisms

## 💾 Data Management & Transferability

### Automatic CSV Export
All IBKR market data is automatically exported to CSV format for:
- **Transferability**: Move data between systems and environments
- **Backup & Archive**: Preserve historical data for compliance and analysis
- **Offline Analysis**: Continue research without live IBKR connection
- **Sharing**: Easy data distribution to team members
- **Speed**: Faster analysis with cached data

### CSV File Structure
```
data/ibkr_{symbol}_{duration}_{barsize}_{timestamp}.csv

Example: data/ibkr_tqqq_3y_1_hour_20250925_120000.csv
```

### Loading Saved Data
```python
# Load most recent data for symbol
data = data_manager.load_from_csv('TQQQ')

# List all saved files
files = data_manager.list_saved_data()
```

## 📞 Support

For technical issues or questions:

1. **Check Documentation**: Review strategy guides and troubleshooting sections
2. **Validate Setup**: Ensure IBKR connection and data subscriptions are proper
3. **Review Logs**: Check notebook output for specific error messages
4. **Test Configuration**: Verify parameter settings and data availability

---

**🏛️ FirstBar Farming Professional Analysis System**
*Institutional-Grade Quantitative Trading Research Platform*

**🤖 Powered by:**
- Interactive Brokers TWS API
- Advanced Performance Analytics
- Professional Risk Management Framework

*Last Updated: September 2024*