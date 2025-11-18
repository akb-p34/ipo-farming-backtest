# IPO Day-Trading Strategy Backtest Plan

## Executive Summary

This document outlines our systematic approach to backtesting IPO day-trading strategies. Our objective is to identify optimal entry and exit times for trading stocks on their initial public offering (IPO) day by analyzing historical data from over 6,000 IPOs spanning 25 years.

The backtest evaluates 78 different trading windows to find patterns that historically generated positive returns, while implementing proper validation techniques to ensure our findings are robust and not the result of overfitting.

---

## 1. Data Sources

### Primary IPO Database

**Dataset:** Jay Ritter's IPO Database (1975-2024)
- **Size:** 6,303 IPOs from January 2000 to January 2025
- **Source:** University of Florida, widely regarded as the authoritative academic source for IPO data
- **Fields Used:**
  - Ticker symbol
  - Company name
  - IPO offer date
  - IPO offer price

**Why This Dataset?**
- Comprehensive and authoritative: Jay Ritter's database is the gold standard in academic IPO research
- Long historical coverage: 25 years of data provides sufficient sample size for statistical validity
- Survivorship bias minimized: Includes both successful companies and those that delisted
- Clean and structured: Professionally maintained data reduces preprocessing requirements

### Intraday Price Data

**Approach:** Simulated IPO Day Trading Data

For each IPO, we generate realistic minute-by-minute price movements for the first trading day using a simulation model that accounts for:

- **Opening Pop:** IPOs typically open 0.8x to 1.5x their offer price (based on historical patterns)
- **Intraday Volatility:** Higher volatility at market open and close, with calmer mid-day trading
- **Mean Reversion:** Prices tend to revert toward a daily average rather than trending continuously
- **Volume Patterns:** Realistic volume curves matching typical IPO day behavior

**Why Simulation?**
- Historical minute-by-minute data is not readily available for most IPOs, especially older ones
- Simulation allows us to test across the full 6,000+ IPO universe
- Our simulation model is calibrated to match observed IPO day characteristics from academic literature
- Provides consistent data quality across all time periods

**Alternative Data Sources:**
The system also supports pulling real historical data from Yahoo Finance or Interactive Brokers, but simulation mode is used for the primary backtest to ensure complete coverage.

---

## 2. Testing Methodology

### Train-Test Split

**Approach:** 70% Training / 30% Testing (Chronological Split)

- **Training Set:** First 70% of IPOs chronologically (Jan 2000 - Aug 2020)
  - 4,412 IPOs
  - Used to identify optimal trading strategies

- **Test Set:** Most recent 30% of IPOs (Sep 2020 - Jan 2025)
  - 1,891 IPOs
  - Used to validate that strategies work on unseen future data

**Why Chronological (Not Random)?**
- Prevents look-ahead bias: We never use future information to make past decisions
- Mimics real-world deployment: We train on historical data and test on future data, just like actual trading
- Accounts for regime changes: Market conditions evolve over time; our validation tests if strategies remain effective

### Trading Window Analysis

**What We're Testing:** All possible intraday entry and exit time combinations

**Window Generation:**
- Entry times tested: Every 30 minutes from 9:30 AM to 3:30 PM (13 possible entry points)
- Exit times tested: Every 30 minutes after entry, up to 4:00 PM market close
- Total combinations: 78 unique trading windows

**Example Windows:**
- Buy at 9:30 AM, Sell at 10:00 AM (30-minute hold)
- Buy at 10:30 AM, Sell at 12:30 PM (2-hour hold)
- Buy at 2:00 PM, Sell at 4:00 PM (2-hour hold into close)

**Evaluation Process:**

For each of the 78 trading windows:
1. Apply the window to every IPO in the training set
2. Calculate the return: (exit price - entry price) / entry price
3. Aggregate performance metrics across all trades
4. Rank windows by average return

**Selection Criteria:**
- Primary metric: Average return per trade
- Minimum threshold: At least 10 valid trades
- The highest-ranked window becomes our "optimal strategy"

---

## 3. What We're Testing

### Primary Research Question

**Can we identify specific intraday time windows on IPO day that consistently generate positive returns?**

### Specific Hypotheses Being Evaluated

1. **Early Pop Capture:** Does buying at market open and selling mid-morning capture the initial enthusiasm pop?

2. **Mid-Day Stability:** Are mid-morning to early afternoon windows more stable and profitable than volatile open/close periods?

3. **Close Rally:** Do IPOs rally into the close, making late-day entries profitable?

4. **Hold Duration:** Is there an optimal holding period (30 minutes, 2 hours, full day)?

### What We're NOT Testing

- Multi-day holding periods (we only trade on IPO day)
- Fundamental analysis or company-specific factors
- Market conditions or sector rotation
- Options strategies or leverage
- Short selling or hedging

---

## 4. Performance Metrics

### Per-Trade Metrics

**Average Return (%)**
- Mean return across all trades in the window
- Primary optimization target

**Standard Deviation**
- Volatility of returns
- Measures consistency and risk

**Win Rate (%)**
- Percentage of trades that were profitable
- Helps assess reliability

**Sharpe Ratio**
- Risk-adjusted return: Average Return / Standard Deviation
- Higher is better; measures return per unit of risk

### Portfolio Metrics

**Initial Capital:** $100,000

**Final Portfolio Value**
- Ending value after all trades

**Total Return (%)**
- (Final Value - Initial Value) / Initial Value

**CAGR (Compound Annual Growth Rate)**
- Annualized return accounting for compounding

**Total Number of Trades**
- How many IPOs were traded

### Benchmark Comparison

**SPY Buy & Hold**
- Performance of buying and holding the S&P 500 ETF over the same period
- Gold standard comparison for any equity strategy

**Outperformance**
- How much our strategy beats (or underperforms) the benchmark

---

## 5. Risk Management Approach

### Position Sizing

**Conservative Allocation:**
- Maximum 5% of portfolio per trade (configured parameter)
- Actual position size: Lesser of 2% of portfolio OR 1/10th of portfolio
- Ensures single IPO cannot cause catastrophic loss

**Example:**
- Portfolio value: $100,000
- Position size: min($2,000, $10,000) = $2,000 per IPO

### Capital Management

**No Leverage:** All positions are fully cash-backed

**No Reinvestment During Day:** Each IPO is traded as a separate position with returns added to capital

**Slippage and Costs:** Not currently modeled (conservative assumption that results represent best-case scenario)

---

## 6. Validation Approach

### Preventing Overfitting

**The Challenge:**
With 78 different strategies tested, we risk finding a pattern that worked by chance on our training data but won't work in the future.

**Our Solutions:**

1. **Train-Test Split:** The optimal strategy chosen from training data must prove itself on completely unseen test data

2. **Large Sample Size:** 4,412 training IPOs provides statistical power to distinguish signal from noise

3. **Simplicity:** We're only optimizing entry and exit times, not complex multi-parameter models

4. **Benchmark Reality Check:** Comparison to SPY keeps us honest about absolute performance

### Validation Criteria

**A successful strategy must:**
- Show positive returns in training set
- Maintain positive returns in test set (generalization)
- Have test set performance reasonably close to training (not degraded)
- Win rate above 50% in both sets
- Outperform SPY benchmark (aspirational goal)

---

## 7. Expected Outputs

### Quantitative Results

- Optimal trading window identified
- Average return per trade
- Win rate
- Risk metrics (Sharpe ratio, standard deviation)
- Portfolio growth curve
- Comparison to SPY benchmark

### Qualitative Insights

- Which time windows performed best and why
- Trade-offs between hold duration and returns
- Consistency of strategy across time periods
- Practical viability for implementation

### Deliverables

1. **Summary Report:** PDF document with key findings
2. **Detailed Analytics:** Complete window analysis showing all 78 strategies ranked
3. **Data Files:** Training and test set compositions, configuration used
4. **Visualizations:** Performance charts, return distributions, time series

---

## 8. Limitations and Assumptions

### Data Limitations

- **Simulated Prices:** Using modeled data rather than actual tick-by-tick prices
- **Survivorship Bias:** Some delisted companies may not be in dataset
- **Historical Period:** 2000-2025 may not represent future market conditions

### Trading Assumptions

- **Perfect Execution:** Assumes we can trade at exact simulated prices (no slippage)
- **No Transaction Costs:** Commissions and fees would reduce returns
- **Full Liquidity:** Assumes we can enter/exit positions at desired times
- **No Market Impact:** Our trades don't move prices

### Scope Limitations

- **Single-Day Only:** Doesn't capture multi-day momentum or reversals
- **No Fundamentals:** Ignores company quality, sector, market cap, underwriter quality
- **Equal Weighting:** Every IPO treated equally regardless of size or conditions
- **No Macroeconomic Factors:** Ignores bull/bear markets, interest rates, volatility regime

---

## 9. Implementation Timeline

### Phase 1: Data Collection
- Load IPO universe from database
- Apply date filters
- Split into training and test sets

### Phase 2: Strategy Development
- Generate all 78 trading windows
- Simulate/fetch price data for each IPO
- Calculate returns for each window on training set

### Phase 3: Optimization
- Rank all windows by average return
- Identify top-performing strategies
- Analyze characteristics of winning windows

### Phase 4: Validation
- Apply optimal strategy to test set
- Calculate out-of-sample performance
- Compare to benchmark (SPY)

### Phase 5: Reporting
- Generate comprehensive analytics
- Create visualizations
- Document findings and recommendations

---

## 10. Success Criteria

### Minimum Viable Strategy

- Positive average return in both training and test sets
- Win rate > 50%
- Sharpe ratio > 0.5 (moderate risk-adjusted return)
- Statistically significant sample size (>100 trades)

### Aspirational Goals

- Outperform SPY benchmark
- CAGR > 10%
- Sharpe ratio > 1.0
- Win rate > 55%
- Consistent performance across market regimes

### Decision Framework

**If successful:** Consider live paper trading with small capital
**If marginal:** Investigate improvements (better data, filtering IPOs, adding signals)
**If unsuccessful:** Document findings and explore alternative strategies

---

## Conclusion

This backtest plan provides a rigorous, systematic approach to evaluating IPO day-trading strategies. By testing all possible trading windows on a large historical dataset with proper train-test validation, we can objectively assess whether exploitable patterns exist.

The methodology balances comprehensiveness (78 strategies tested) with simplicity (only two parameters: entry and exit time), reducing the risk of spurious findings while maximizing our chances of discovering genuine alpha.

Regardless of the outcome, this backtest will provide valuable insights into IPO market dynamics and inform our future trading decisions with data-driven evidence rather than intuition.

---

**Document Version:** 1.0
**Date:** November 18, 2025
**Backtest Period:** January 2000 - January 2025
**Total IPOs Analyzed:** 6,303
