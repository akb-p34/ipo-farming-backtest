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
        for idx, row in self.ipo_universe.iterrows():
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

            if progress_callback and idx % 100 == 0:
                progress_callback(0.3 + (idx/total) * 0.3, f"Collecting data: {idx}/{total}")

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
                    progress_callback(0.6 + (window_count/total_windows) * 0.2,
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
        train_portfolio = self.simulate_portfolio(self.train_universe, self.optimal_strategy)
        test_portfolio = self.simulate_portfolio(self.test_universe, self.optimal_strategy)

        # Save results
        self.results = {
            'split_info': split_info,
            'optimal_strategy': self.optimal_strategy.to_dict(),
            'train_portfolio': train_portfolio,
            'test_portfolio': test_portfolio,
            'output_dir': str(self.output_dir)
        }

        with open(self.output_dir / 'analysis' / 'backtest_results.json', 'w') as f:
            json.dump(self.results, f, indent=2, default=str)

        if progress_callback:
            progress_callback(1.0, "Backtest complete!")

        return self.results