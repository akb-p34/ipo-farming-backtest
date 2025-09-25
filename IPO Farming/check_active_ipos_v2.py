#!/usr/bin/env python3
"""
check_active_ipos_v2.py
-----------------------
Reads a Jay Ritter-style IPO Excel (e.g., "IPO-age.xlsx"), filters IPOs since a chosen date,
checks which tickers still trade using Yahoo Finance (yfinance), and writes two CSVs.

Changes from v1:
- Verbose logging (--verbose) so you can see progress.
- Prints where outputs are saved and lists files in --outdir.
- Ensures --outdir exists.
- More robust yfinance "is active" heuristic with a fallback.
"""

import argparse
import os
import sys
import time
from datetime import datetime
import pandas as pd

def install_and_import(package, quiet=False):
    import importlib
    try:
        return importlib.import_module(package)
    except ImportError:
        if not quiet:
            print(f"[INFO] Installing missing package: {package}", file=sys.stderr)
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        return importlib.import_module(package)

def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=str, default="IPO-age.xlsx", help="Path to the IPO Excel file")
    ap.add_argument("--sheet", type=str, default="1975-2024", help="Worksheet name")
    ap.add_argument("--since", type=str, default="2000-01-01", help="Earliest IPO date to include (YYYY-MM-DD)")
    ap.add_argument("--outdir", type=str, default=".", help="Output directory")
    ap.add_argument("--sleep", type=float, default=0.4, help="Seconds to sleep between API calls")
    ap.add_argument("--max", type=int, default=None, help="Optional cap on number of tickers to check (for testing)")
    ap.add_argument("--verbose", action="store_true", help="Print progress information")
    return ap.parse_args()

def load_ipos(xlsx_path, sheet, since_str, verbose=False):
    if verbose:
        print(f"[INFO] Reading Excel: {xlsx_path} (sheet='{sheet}')", file=sys.stderr)
    df = pd.read_excel(xlsx_path, sheet_name=sheet, dtype={"offer date": str})
    keep_cols = ["offer date", "IPO name", "Ticker"]
    for col in keep_cols:
        if col not in df.columns:
            raise ValueError(f"Expected column '{col}' not found in sheet '{sheet}'. Columns present: {df.columns.tolist()}")

    ipo = df[keep_cols].copy()
    ipo["offer date"] = pd.to_datetime(ipo["offer date"], format="%Y%m%d", errors="coerce")
    since_dt = pd.to_datetime(since_str)
    ipo = ipo[ipo["offer date"] >= since_dt]
    ipo = ipo.dropna(subset=["Ticker"])
    ipo["Ticker"] = ipo["Ticker"].astype(str).str.strip()
    ipo = ipo.drop_duplicates(subset=["Ticker", "offer date"], keep="first").reset_index(drop=True)
    if verbose:
        print(f"[INFO] IPOs after {since_str}: {len(ipo)} rows", file=sys.stderr)
    return ipo

def is_active_yf(ticker, yf_mod):
    """
    Heuristics to decide if a ticker is still 'active' on Yahoo:
    1) Try recent daily history.
    2) Fallback: use fast_info.last_price or info['regularMarketPrice'] if available.
    """
    try:
        tk = yf_mod.Ticker(ticker)
        hist = tk.history(period="5d", interval="1d", auto_adjust=False, actions=False)
        if hist is None or hist.empty:
            hist = tk.history(period="1mo", interval="1d", auto_adjust=False, actions=False)
        if hist is not None and not hist.empty and "Close" in hist.columns and hist["Close"].notna().any():
            return True, "ok_hist"
        # Fallback checks
        try:
            fi = getattr(tk, "fast_info", None)
            if fi and hasattr(fi, "last_price") and fi.last_price is not None:
                return True, "ok_fast_info"
        except Exception:
            pass
        try:
            info = tk.info or {}
            if info.get("regularMarketPrice") not in (None, 0):
                return True, "ok_info"
        except Exception:
            pass
        return False, "no_data"
    except Exception as e:
        return False, f"error:{type(e).__name__}"

def main():
    args = parse_args()
    if args.verbose:
        print(f"[INFO] Python: {sys.executable}", file=sys.stderr)
        print(f"[INFO] CWD: {os.getcwd()}", file=sys.stderr)
        print(f"[INFO] Output dir: {os.path.abspath(args.outdir)}", file=sys.stderr)

    # Make sure outdir exists
    os.makedirs(args.outdir, exist_ok=True)

    # Dependencies
    pd.options.mode.copy_on_write = True
    yf = install_and_import("yfinance")

    # Load IPOs
    ipo = load_ipos(args.input, args.sheet, args.since, verbose=args.verbose)

    if len(ipo) == 0:
        print("[WARN] No IPO rows after filtering. Check --since date, sheet name, or file.", file=sys.stderr)

    # Optional cap
    to_check = ipo if args.max is None else ipo.iloc[: args.max].copy()
    if args.verbose:
        print(f"[INFO] Checking {len(to_check)} tickers (sleep={args.sleep}s)", file=sys.stderr)

    results = []
    start = time.time()
    for idx, row in to_check.iterrows():
        tkr = row["Ticker"]
        comp = row["IPO name"]
        dte = row["offer date"]
        active, note = is_active_yf(tkr, yf)
        results.append({
            "Ticker": tkr,
            "Company": comp,
            "IPO_Date": dte.date() if isinstance(dte, pd.Timestamp) else dte,
            "Active": bool(active),
            "Check_Note": note,
        })
        if args.verbose:
            print(f"[{idx+1}/{len(to_check)}] {tkr:10s} -> {'ACTIVE' if active else 'INACTIVE'} ({note})", file=sys.stderr)
        time.sleep(args.sleep)

    out = pd.DataFrame(results)

    # Split & save
    active_df = out[out["Active"]].copy()
    inactive_df = out[~out["Active"]].copy()

    # Sort nicely
    active_df = active_df.sort_values(["IPO_Date", "Ticker"]).reset_index(drop=True)
    inactive_df = inactive_df.sort_values(["IPO_Date", "Ticker"]).reset_index(drop=True)

    active_path = os.path.join(args.outdir, "active_ipos_since_2000.csv")
    inactive_path = os.path.join(args.outdir, "inactive_or_delisted_ipos_since_2000.csv")
    log_path = os.path.join(args.outdir, "ipo_activity_check_log.csv")

    active_df.to_csv(active_path, index=False)
    inactive_df.to_csv(inactive_path, index=False)
    out.to_csv(log_path, index=False)

    # Final summary
    print(f"[DONE] Saved files to: {os.path.abspath(args.outdir)}")
    print(f"  ACTIVE  -> {active_path}")
    print(f"  INACTIVE-> {inactive_path}")
    print(f"  LOG     -> {log_path}")
    try:
        files = sorted(os.listdir(args.outdir))
        print("\n[DIR LIST]")
        for f in files:
            print(" ", f)
    except Exception:
        pass

if __name__ == "__main__":
    main()
