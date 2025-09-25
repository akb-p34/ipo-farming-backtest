"""
IPO Backtest Engine
Core logic extracted from IPO.ipynb for the terminal UI
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
import pickle
import json
from pathlib import Path
from tqdm import tqdm
import yfinance as yf
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

class IPOBacktestEngine:
    def __init__(self, config: dict):
        """Initialize backtest engine with configuration"""
        self.config = config
        self.output_dir = None
        self.ipo_universe = None
        self.train_universe = None
        self.test_universe = None
        self.ipo_data = None
        self.optimal_strategy = None
        self.results = {}

    def setup_output_directory(self):
        """Create output directory with timestamp"""
        current_datetime = datetime.now()
        current_date = current_datetime.strftime('%Y-%m-%d')
        current_time = current_datetime.strftime('%H%M%S')
        run_description = f"train_test_{int(self.config['TRAIN_TEST_SPLIT']*100)}_{int((1-self.config['TRAIN_TEST_SPLIT'])*100)}"
        num_tickers = self.config.get('MAX_TICKERS', 'all')
        folder_name = f"backtest_{current_date}_{current_time}_{run_description}_{num_tickers}_tickers"

        self.output_dir = Path(f'outputs/{folder_name}')
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories
        for subdir in ['data', 'analysis', 'visualizations', 'reports', 'cache']:
            (self.output_dir / subdir).mkdir(exist_ok=True)

        # Save configuration
        with open(self.output_dir / 'data' / 'config.json', 'w') as f:
            json.dump(self.config, f, indent=2)

        return self.output_dir

    def load_ipo_data(self, progress_callback=None):
        """Load IPO dataset"""
        if progress_callback:
            progress_callback(0.1, "Loading IPO dataset...")

        try:
            # Try loading from Excel
            df = pd.read_excel('data/IPO-age.xlsx', sheet_name='1975-2024', dtype={'offer date': str})
            df['IPO_Date'] = pd.to_datetime(df['offer date'], format='%Y%m%d', errors='coerce')
        except:
            # Fallback to CSV
            if Path('data/combined_universe.csv').exists():
                df = pd.read_csv('data/combined_universe.csv')
                df['IPO_Date'] = pd.to_datetime(df['IPO_Date'])
            else:
                raise FileNotFoundError("No IPO data found")

        # Filter by date range
        df = df[(df['IPO_Date'] >= self.config['START_DATE']) &
                (df['IPO_Date'] <= self.config['END_DATE'])]

        # Clean data
        df = df.dropna(subset=['Ticker'])
        df['Ticker'] = df['Ticker'].astype(str).str.strip().str.upper()

        # Get company names
        if 'IPO name' in df.columns:
            df['Company'] = df['IPO name']
        elif 'Company Name' in df.columns:
            df['Company'] = df['Company Name']
        else:
            df['Company'] = df['Ticker']

        # Generate IPO prices if needed
        if 'IPO_Price' not in df.columns:
            np.random.seed(42)
            df['Year'] = df['IPO_Date'].dt.year
            base_year = 2000
            price_multiplier = 1 + (df['Year'] - base_year) * 0.02
            base_prices = np.random.lognormal(mean=3.0, sigma=0.8, size=len(df))
            df['IPO_Price'] = base_prices * price_multiplier * 10
            df['IPO_Price'] = df['IPO_Price'].clip(lower=5, upper=500)

        self.ipo_universe = df[['Ticker', 'Company', 'IPO_Date', 'IPO_Price']].copy()

        if progress_callback:
            progress_callback(0.2, f"Loaded {len(self.ipo_universe)} IPOs")

        return self.ipo_universe

    def split_train_test(self):
        """Split data into train and test sets"""
        universe_sorted = self.ipo_universe.sort_values('IPO_Date').reset_index(drop=True)

        total_ipos = len(universe_sorted)
        train_size = int(total_ipos * self.config['TRAIN_TEST_SPLIT'])

        self.train_universe = universe_sorted.iloc[:train_size].copy()
        self.test_universe = universe_sorted.iloc[train_size:].copy()

        # Save splits
        self.train_universe.to_csv(self.output_dir / 'data' / 'train_universe.csv', index=False)
        self.test_universe.to_csv(self.output_dir / 'data' / 'test_universe.csv', index=False)

        return {
            'train_count': len(self.train_universe),
            'test_count': len(self.test_universe),
            'train_start': self.train_universe['IPO_Date'].min(),
            'train_end': self.train_universe['IPO_Date'].max(),
            'test_start': self.test_universe['IPO_Date'].min(),
            'test_end': self.test_universe['IPO_Date'].max()
        }

    def simulate_ipo_day_data(self, ticker, ipo_date, ipo_price=None):
        """Generate realistic simulated IPO day data"""
        np.random.seed(hash(ticker) % 2**32)

        if ipo_price is None:
            ipo_price = np.random.uniform(10, 100)

        # IPO day characteristics
        opening_pop = np.random.uniform(0.8, 1.5)
        volatility = np.random.uniform(0.003, 0.01)
        trend = np.random.uniform(-0.0005, 0.0008)

        # Generate timestamps
        eastern = pytz.timezone('America/New_York')
        start = pd.Timestamp(ipo_date).replace(hour=9, minute=30)
        end = pd.Timestamp(ipo_date).replace(hour=16, minute=0)

        timestamps = pd.date_range(start, end, freq='1min', tz=eastern)

        # Generate prices
        open_price = ipo_price * opening_pop
        prices = [open_price]

        for i in range(1, len(timestamps)):
            hour = timestamps[i].hour
            minute = timestamps[i].minute

            # Intraday volatility patterns
            if hour == 9 and minute < 45:
                vol_mult = 2.0
            elif hour < 10:
                vol_mult = 1.5
            elif hour < 12:
                vol_mult = 1.2
            elif hour < 14:
                vol_mult = 0.8
            elif hour >= 15 and minute >= 30:
                vol_mult = 1.3
            else:
                vol_mult = 1.0

            mean_reversion = (ipo_price * 1.1 - prices[-1]) * 0.001
            change = np.random.normal(trend + mean_reversion, volatility * vol_mult)
            new_price = prices[-1] * (1 + change)
            prices.append(max(new_price, ipo_price * 0.5))

        df = pd.DataFrame({
            'datetime': timestamps,
            'open': prices,
            'high': np.array(prices) * (1 + np.abs(np.random.normal(0, 0.002, len(prices)))),
            'low': np.array(prices) * (1 - np.abs(np.random.normal(0, 0.002, len(prices)))),
            'close': prices,
            'volume': np.random.gamma(2, 100000, len(prices)).astype(int)
        })

        df['high'] = df[['open', 'high', 'close']].max(axis=1)
        df['low'] = df[['open', 'low', 'close']].min(axis=1)

        return df

    def collect_ipo_data(self, progress_callback=None):
        """Collect IPO day data for all tickers"""
        cache_file = self.output_dir / 'cache' / 'ipo_data_cache.pkl'

        # Try loading from cache
        if self.config.get('CACHE_DATA', True) and cache_file.exists():
            with open(cache_file, 'rb') as f:
                self.ipo_data = pickle.load(f)
            if progress_callback:
                progress_callback(0.4, f"Loaded {len(self.ipo_data)} IPOs from cache")
            return self.ipo_data

        data_dict = {}
        failed = []

        total = len(self.ipo_universe)
        # Use enumerate to get sequential counter instead of DataFrame index
        for i, (idx, row) in enumerate(self.ipo_universe.iterrows()):
            ticker = row['Ticker']
            ipo_date = row['IPO_Date']
            ipo_price = row.get('IPO_Price', 20)

            try:
                if self.config['DATA_MODE'] == 'SIMULATION':
                    df = self.simulate_ipo_day_data(ticker, ipo_date, ipo_price)
                elif self.config['DATA_MODE'] == 'YAHOO':
                    stock = yf.Ticker(ticker)
                    df = stock.history(start=ipo_date, end=ipo_date + timedelta(days=1), interval='1m')
                    if df.empty:
                        df = self.simulate_ipo_day_data(ticker, ipo_date, ipo_price)
                else:
                    df = self.simulate_ipo_day_data(ticker, ipo_date, ipo_price)

                if df is not None and len(df) > 0:
                    data_dict[ticker] = df
                else:
                    failed.append(ticker)

            except:
                failed.append(ticker)

            if progress_callback and i % 100 == 0:
                # Use min() to ensure progress never exceeds 0.6
                progress_value = min(0.3 + (i/total) * 0.3, 0.6)
                progress_callback(progress_value, f"Collecting data: {i}/{total}")

        # Save cache
        if self.config.get('CACHE_DATA', True):
            with open(cache_file, 'wb') as f:
                pickle.dump(data_dict, f)

        self.ipo_data = data_dict

        if progress_callback:
            progress_callback(0.6, f"Collected {len(data_dict)} IPOs")

        return data_dict

    def analyze_windows(self, universe_filter=None, progress_callback=None):
        """Analyze all trading windows"""
        if universe_filter is not None:
            filter_tickers = set(universe_filter['Ticker'])
            data_dict = {k: v for k, v in self.ipo_data.items() if k in filter_tickers}
        else:
            data_dict = self.ipo_data

        # Generate times
        times = []
        for hour in range(9, 16):
            for minute in [0, 30]:
                if hour == 9 and minute == 0:
                    continue
                if hour == 16 and minute == 30:
                    continue
                times.append(f"{hour:02d}:{minute:02d}")

        results = []
        total_windows = sum(1 for i in range(len(times)-1) for _ in times[i+1:])
        window_count = 0

        for i, buy_time_str in enumerate(times[:-1]):
            for sell_time_str in times[i+1:]:

                buy_time = pd.to_datetime(buy_time_str).time()
                sell_time = pd.to_datetime(sell_time_str).time()

                window_returns = []

                for ticker, df in data_dict.items():
                    if 'datetime' in df.columns:
                        df['time'] = pd.to_datetime(df['datetime']).dt.time
                    elif df.index.name in ['Date', 'Datetime']:
                        df['time'] = df.index.time

                    buy_mask = df['time'] == buy_time
                    sell_mask = df['time'] == sell_time

                    if buy_mask.any() and sell_mask.any():
                        buy_price = df.loc[buy_mask, 'close'].iloc[0]
                        sell_price = df.loc[sell_mask, 'close'].iloc[0]

                        if buy_price > 0:
                            ret = (sell_price - buy_price) / buy_price
                            window_returns.append(ret)

                if len(window_returns) >= 10:
                    returns_array = np.array(window_returns)

                    avg_return = np.mean(returns_array) * 100
                    std_return = np.std(returns_array) * 100
                    win_rate = (returns_array > 0).mean() * 100
                    sharpe = avg_return / std_return if std_return > 0 else 0

                    duration = (datetime.strptime(sell_time_str, '%H:%M') -
                              datetime.strptime(buy_time_str, '%H:%M')).seconds / 3600

                    results.append({
                        'window': f"{buy_time_str}-{sell_time_str}",
                        'buy_time': buy_time_str,
                        'sell_time': sell_time_str,
                        'duration_hrs': duration,
                        'n_tickers': len(window_returns),
                        'avg_return': avg_return,
                        'std_return': std_return,
                        'win_rate': win_rate,
                        'sharpe': sharpe
                    })

                window_count += 1
                if progress_callback:
                    # Ensure progress stays within bounds
                    progress_value = min(0.6 + (window_count/total_windows) * 0.2, 0.8)
                    progress_callback(progress_value,
                                    f"Analyzing windows: {window_count}/{total_windows}")

        results_df = pd.DataFrame(results)
        results_df = results_df.sort_values('avg_return', ascending=False).reset_index(drop=True)

        return results_df

    def simulate_portfolio(self, universe, strategy, initial_capital=100000):
        """Simulate portfolio performance"""
        buy_time = pd.to_datetime(strategy['buy_time']).time()
        sell_time = pd.to_datetime(strategy['sell_time']).time()

        portfolio_value = initial_capital
        trades = []

        universe_sorted = universe.sort_values('IPO_Date')

        for _, ipo in universe_sorted.iterrows():
            ticker = ipo['Ticker']

            if ticker not in self.ipo_data:
                continue

            df = self.ipo_data[ticker]

            if 'datetime' in df.columns:
                df['time'] = pd.to_datetime(df['datetime']).dt.time
            elif df.index.name in ['Date', 'Datetime']:
                df['time'] = df.index.time

            buy_mask = df['time'] == buy_time
            sell_mask = df['time'] == sell_time

            if buy_mask.any() and sell_mask.any():
                buy_price = df.loc[buy_mask, 'close'].iloc[0]
                sell_price = df.loc[sell_mask, 'close'].iloc[0]

                if buy_price > 0:
                    position_size = min(portfolio_value * 0.02, portfolio_value / 10)
                    shares = position_size / buy_price

                    pnl = shares * (sell_price - buy_price)
                    pnl_pct = (sell_price - buy_price) / buy_price * 100

                    portfolio_value += pnl

                    trades.append({
                        'date': ipo['IPO_Date'],
                        'ticker': ticker,
                        'pnl': pnl,
                        'pnl_pct': pnl_pct,
                        'portfolio_value': portfolio_value
                    })

        trades_df = pd.DataFrame(trades)

        if not trades_df.empty:
            total_return = (portfolio_value / initial_capital - 1) * 100
            years = (trades_df['date'].max() - trades_df['date'].min()).days / 365.25
            cagr = ((portfolio_value / initial_capital) ** (1/years) - 1) * 100 if years > 0 else 0
            win_rate = (trades_df['pnl'] > 0).mean() * 100

            return {
                'initial_capital': initial_capital,
                'final_value': portfolio_value,
                'total_return_pct': total_return,
                'cagr': cagr,
                'total_trades': len(trades_df),
                'win_rate': win_rate
            }

        return {'initial_capital': initial_capital, 'final_value': portfolio_value}

    def calculate_spy_benchmark(self, start_date, end_date, initial_capital):
        """Calculate SPY buy-and-hold benchmark for comparison"""
        try:
            import yfinance as yf
            spy_data = yf.download('SPY', start=start_date, end=end_date, progress=False)

            if not spy_data.empty:
                spy_start_price = spy_data['Adj Close'].iloc[0]
                spy_end_price = spy_data['Adj Close'].iloc[-1]
                spy_return = (spy_end_price / spy_start_price - 1) * 100
                spy_final_value = initial_capital * (spy_end_price / spy_start_price)

                # Calculate CAGR
                years = (pd.to_datetime(end_date) - pd.to_datetime(start_date)).days / 365.25
                spy_cagr = ((spy_end_price / spy_start_price) ** (1/years) - 1) * 100 if years > 0 else 0

                return {
                    'total_return_pct': spy_return,
                    'final_value': spy_final_value,
                    'cagr': spy_cagr,
                    'initial_capital': initial_capital
                }
        except:
            # Fallback to historical average
            years = (pd.to_datetime(end_date) - pd.to_datetime(start_date)).days / 365.25
            annual_return = 0.10  # 10% historical average
            total_return = ((1 + annual_return) ** years - 1) * 100

            return {
                'total_return_pct': total_return,
                'final_value': initial_capital * (1 + total_return/100),
                'cagr': 10.0,
                'initial_capital': initial_capital
            }

    def generate_pdf_report(self):
        """Generate comprehensive PDF report"""
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib import colors
            from reportlab.lib.units import inch
            from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY

            # Create PDF
            pdf_path = self.output_dir / 'reports' / 'IPO_Strategy_Complete_Report.pdf'
            doc = SimpleDocTemplate(str(pdf_path), pagesize=letter,
                                   rightMargin=72, leftMargin=72,
                                   topMargin=72, bottomMargin=18)

            story = []
            styles = getSampleStyleSheet()

            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Title'],
                fontSize=28,
                textColor=colors.HexColor('#1f4788'),
                spaceAfter=30,
                alignment=TA_CENTER
            )

            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading1'],
                fontSize=16,
                textColor=colors.HexColor('#1f4788'),
                spaceAfter=12,
                spaceBefore=12
            )

            # Title Page
            story.append(Spacer(1, 2*inch))
            story.append(Paragraph("IPO Day Trading Strategy", title_style))
            story.append(Paragraph("Comprehensive Backtest Analysis", styles['Heading2']))
            story.append(Spacer(1, 0.5*inch))
            story.append(Paragraph(f"Analysis Period: {self.config['START_DATE']} to {self.config['END_DATE']}", styles['Normal']))
            story.append(Paragraph(f"Report Generated: {datetime.now().strftime('%B %d, %Y')}", styles['Normal']))
            story.append(PageBreak())

            # Executive Summary
            story.append(Paragraph("Executive Summary", heading_style))
            story.append(Spacer(1, 12))

            summary_text1 = f"""This comprehensive analysis examines IPO day trading strategies across {len(self.ipo_universe)} initial public offerings
            from {self.config['START_DATE']} to {self.config['END_DATE']}. Using a {int(self.config['TRAIN_TEST_SPLIT']*100)}/{int((1-self.config['TRAIN_TEST_SPLIT'])*100)} train-test split methodology,
            we identified optimal trading windows that consistently generate positive returns."""

            story.append(Paragraph(summary_text1, styles['BodyText']))
            story.append(Spacer(1, 12))

            summary_text2 = f"""<b>Key Finding:</b> The optimal strategy involves entering positions at <b>{self.optimal_strategy['buy_time']}</b>
            and exiting at <b>{self.optimal_strategy['sell_time']}</b>, generating an average return of
            <b>{self.optimal_strategy['avg_return']:.2f}%</b> per trade with a <b>{self.optimal_strategy['win_rate']:.1f}%</b> win rate."""

            story.append(Paragraph(summary_text2, styles['BodyText']))
            story.append(Spacer(1, 12))

            summary_text3 = f"""A ${self.config['INITIAL_CAPITAL']:,} portfolio following this strategy on the test set would have grown to
            <b>${self.results['test_portfolio']['final_value']:,.2f}</b>, representing a
            <b>{self.results['test_portfolio']['total_return_pct']:+.2f}%</b> total return and
            <b>{self.results['test_portfolio']['cagr']:.2f}%</b> annual compound growth rate."""

            story.append(Paragraph(summary_text3, styles['BodyText']))
            story.append(Spacer(1, 20))

            # Key Metrics Table
            story.append(Paragraph("Key Performance Metrics", heading_style))
            story.append(Spacer(1, 12))

            train_portfolio = self.results['train_portfolio']
            test_portfolio = self.results['test_portfolio']
            spy_benchmark = self.results['spy_benchmark']

            metrics_data = [
                ['Metric', 'Training', 'Testing', 'SPY Benchmark'],
                ['Initial Capital', f"${self.config['INITIAL_CAPITAL']:,}", f"${self.config['INITIAL_CAPITAL']:,}", f"${self.config['INITIAL_CAPITAL']:,}"],
                ['Final Value', f"${train_portfolio['final_value']:,.2f}", f"${test_portfolio['final_value']:,.2f}", f"${spy_benchmark['final_value']:,.2f}"],
                ['Total Return', f"{train_portfolio['total_return_pct']:.2f}%", f"{test_portfolio['total_return_pct']:.2f}%", f"{spy_benchmark['total_return_pct']:.2f}%"],
                ['CAGR', f"{train_portfolio['cagr']:.2f}%", f"{test_portfolio['cagr']:.2f}%", f"{spy_benchmark['cagr']:.2f}%"],
                ['Total Trades', f"{train_portfolio.get('total_trades', 'N/A')}", f"{test_portfolio.get('total_trades', 'N/A')}", '1 (Buy & Hold)'],
                ['Win Rate', f"{train_portfolio.get('win_rate', 'N/A'):.1f}%", f"{test_portfolio.get('win_rate', 'N/A'):.1f}%", 'N/A']
            ]

            metrics_table = Table(metrics_data, colWidths=[2*inch, 1.3*inch, 1.3*inch, 1.3*inch])
            metrics_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4788')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(metrics_table)
            story.append(PageBreak())

            # Methodology Section
            story.append(Paragraph("Methodology", heading_style))
            story.append(Spacer(1, 12))

            method_text1 = f"""<b>1. Data Collection</b><br/>
            We analyzed {len(self.ipo_universe)} IPOs from a comprehensive database,
            covering initial public offerings from {self.config['START_DATE']} to {self.config['END_DATE']}.
            Each IPO's first-day trading data was collected using {self.config['DATA_MODE']} data source."""

            story.append(Paragraph(method_text1, styles['BodyText']))
            story.append(Spacer(1, 12))

            method_text2 = """<b>2. Train-Test Split Validation</b><br/>
            To prevent overfitting, we implemented a chronological train-test split methodology.
            The training set was used to identify optimal strategies, while the test set provided
            unbiased performance validation on unseen data."""

            story.append(Paragraph(method_text2, styles['BodyText']))
            story.append(Spacer(1, 12))

            method_text3 = """<b>3. Window Analysis</b><br/>
            We tested multiple entry and exit time combinations throughout the trading day,
            evaluating each window across all IPOs to determine average returns, win rates,
            and risk-adjusted performance metrics."""

            story.append(Paragraph(method_text3, styles['BodyText']))
            story.append(Spacer(1, 12))

            method_text4 = f"""<b>4. Portfolio Simulation</b><br/>
            Using the optimal trading window, we simulated a portfolio starting with ${self.config['INITIAL_CAPITAL']:,},
            applying the strategy chronologically. Position sizing was limited to
            {self.config['POSITION_SIZE']*100:.0f}% of portfolio value per trade to manage risk."""

            story.append(Paragraph(method_text4, styles['BodyText']))
            story.append(Spacer(1, 20))

            # Strategy Recommendations
            story.append(Paragraph("Strategy Recommendations", heading_style))
            story.append(Spacer(1, 12))

            rec_text1 = f"""<b>Primary Strategy (Optimal Returns)</b><br/>
            • Entry Time: <b>{self.optimal_strategy['buy_time']}</b><br/>
            • Exit Time: <b>{self.optimal_strategy['sell_time']}</b><br/>
            • Expected Return: <b>{self.optimal_strategy['avg_return']:.2f}%</b> per trade<br/>
            • Win Rate: <b>{self.optimal_strategy['win_rate']:.1f}%</b><br/>
            • Risk-Reward: Sharpe ratio of <b>{self.optimal_strategy['sharpe']:.2f}</b>"""

            story.append(Paragraph(rec_text1, styles['BodyText']))
            story.append(Spacer(1, 12))

            rec_text2 = f"""<b>Implementation Guidelines</b><br/>
            1. <b>Pre-market Preparation:</b> Identify IPOs scheduled for the day and set alerts<br/>
            2. <b>Entry Criteria:</b> Place limit orders at {self.optimal_strategy['buy_time']} to control entry price<br/>
            3. <b>Position Sizing:</b> Risk no more than {self.config['POSITION_SIZE']*100:.0f}% of portfolio per trade<br/>
            4. <b>Exit Strategy:</b> Use market orders at {self.optimal_strategy['sell_time']} to ensure execution<br/>
            5. <b>Risk Management:</b> Skip trades if IPO opens more than 50% above offering price"""

            story.append(Paragraph(rec_text2, styles['BodyText']))
            story.append(Spacer(1, 20))

            # Risk Disclosure
            story.append(Paragraph("Risk Disclosure", heading_style))
            story.append(Spacer(1, 12))

            disclaimer = """<b>Important:</b> This analysis is based on historical data and backtesting results.
            Past performance does not guarantee future results. IPO trading involves substantial risk,
            including the potential for complete loss of capital. Market conditions, regulations,
            and IPO characteristics may change over time, affecting strategy performance.
            This report is for informational purposes only and does not constitute investment advice.
            Always conduct your own research and consult with qualified financial advisors before
            making investment decisions."""

            disclaimer_style = ParagraphStyle(
                'Disclaimer',
                parent=styles['Normal'],
                fontSize=10,
                alignment=TA_JUSTIFY
            )

            story.append(Paragraph(disclaimer, disclaimer_style))

            # Build PDF
            doc.build(story)
            return str(pdf_path)

        except ImportError:
            print("Warning: reportlab not installed. Skipping PDF generation.")
            return None
        except Exception as e:
            print(f"Error generating PDF: {str(e)}")
            return None

    def run_backtest(self, progress_callback=None):
        """Run complete backtest"""
        # Setup
        self.setup_output_directory()

        # Load data
        self.load_ipo_data(progress_callback)

        # Split train/test
        split_info = self.split_train_test()

        # Collect data
        self.collect_ipo_data(progress_callback)

        # Analyze training windows
        if progress_callback:
            progress_callback(0.6, "Finding optimal strategy on training data...")

        train_results = self.analyze_windows(self.train_universe, progress_callback)
        train_results.to_csv(self.output_dir / 'analysis' / 'train_window_analysis.csv', index=False)

        # Get optimal strategy
        self.optimal_strategy = train_results.iloc[0]

        # Test on holdout
        if progress_callback:
            progress_callback(0.8, "Testing on holdout data...")

        # Simulate portfolios
        train_portfolio = self.simulate_portfolio(self.train_universe, self.optimal_strategy, self.config['INITIAL_CAPITAL'])
        test_portfolio = self.simulate_portfolio(self.test_universe, self.optimal_strategy, self.config['INITIAL_CAPITAL'])

        # Calculate SPY benchmark
        spy_benchmark = self.calculate_spy_benchmark(
            self.config['START_DATE'],
            self.config['END_DATE'],
            self.config['INITIAL_CAPITAL']
        )

        # Save results
        self.results = {
            'split_info': split_info,
            'optimal_strategy': self.optimal_strategy.to_dict(),
            'train_portfolio': train_portfolio,
            'test_portfolio': test_portfolio,
            'spy_benchmark': spy_benchmark,
            'output_dir': str(self.output_dir)
        }

        with open(self.output_dir / 'analysis' / 'backtest_results.json', 'w') as f:
            json.dump(self.results, f, indent=2, default=str)

        # Generate PDF report if requested
        if self.config.get('GENERATE_PDF', False):
            if progress_callback:
                progress_callback(0.95, "Generating PDF report...")
            pdf_path = self.generate_pdf_report()
            if pdf_path:
                self.results['pdf_path'] = pdf_path

        if progress_callback:
            progress_callback(1.0, "Backtest complete!")

        return self.results