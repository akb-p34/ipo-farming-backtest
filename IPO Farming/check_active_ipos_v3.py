#!/usr/bin/env python3
"""
check_active_ipos_v3.py
-----------------------
Reads a Jay Ritter-style IPO Excel (e.g., "IPO-age.xlsx"), filters IPOs since a chosen date,
and determines which tickers are still publicly listed by probing Yahoo Finance with a light
"daily" or "weekly" heartbeat (no bulk data download).

Outputs two CSVs in --outdir:
  - active_ipos_since_<YYYY-MM-DD>.csv
  - inactive_or_delisted_ipos_since_<YYYY-MM-DD>.csv

Usage examples:
  python3 check_active_ipos_v3.py --input IPO-age.xlsx --sheet "1975-2024" --since 2000-01-01 --freq daily  --outdir . --verbose
  python3 check_active_ipos_v3.py --input IPO-age.xlsx --sheet "1975-2024" --since 2015-01-01 --freq weekly --outdir . --verbose

Notes:
- "Active" means Yahoo Finance can return *some* recent OHLC for the ticker at the requested frequency.
- This is a heuristic. For research-grade classification, cross-check with CRSP or official exchange masters.
"""

import argparse
import os
import sys
import time
from datetime import datetime
import pandas as pd

FREQ_OPTIONS = ("daily", "weekly")

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
    ap.add_argument("--freq", type=str, default="daily", choices=FREQ_OPTIONS, help="Light check frequency: daily or weekly")
    ap.add_argument("--outdir", type=str, default=".", help="Output directory")
    ap.add_argument("--sleep", type=float, default=0.3, help="Seconds to sleep between API calls (politeness)")
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

def is_active_yf_light(ticker, yf_mod, freq="daily"):
    """
    Minimal probe:
      - daily: request 5d of 1d bars
      - weekly: request ~3mo of 1wk bars
    We do not persist the data; we only check for any valid OHLC values.
    """
    try:
        tk = yf_mod.Ticker(ticker)
        if freq == "weekly":
            hist = tk.history(period="3mo", interval="1wk", auto_adjust=False, actions=False)
        else:
            hist = tk.history(period="5d", interval="1d", auto_adjust=False, actions=False)

        if hist is not None and not hist.empty:
            # Require Close present and non-NaN to be safe
            if "Close" in hist.columns and hist["Close"].notna().any():
                return True, f"ok_{freq}"
        # Fallbacks: attempt fast_info or info without pulling large frames
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
        print(f"[INFO] Using frequency check: {args.freq}", file=sys.stderr)

    os.makedirs(args.outdir, exist_ok=True)

    # Dependencies
    pd.options.mode.copy_on_write = True
    yf = install_and_import("yfinance")

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
        active, note = is_active_yf_light(tkr, yf, freq=args.freq)
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
    since_tag = pd.to_datetime(args.since).date().isoformat()

    # Split & save (keep IPO_Date attached)
    active_df = out[out["Active"]][["Ticker", "Company", "IPO_Date"]].sort_values(["IPO_Date", "Ticker"]).reset_index(drop=True)
    inactive_df = out[~out["Active"]][["Ticker", "Company", "IPO_Date"]].sort_values(["IPO_Date", "Ticker"]).reset_index(drop=True)

    active_path = os.path.join(args.outdir, f"active_ipos_since_{since_tag}.csv")
    inactive_path = os.path.join(args.outdir, f"inactive_or_delisted_ipos_since_{since_tag}.csv")
    log_path = os.path.join(args.outdir, f"ipo_activity_check_log_since_{since_tag}.csv")

    active_df.to_csv(active_path, index=False)
    inactive_df.to_csv(inactive_path, index=False)
    out.to_csv(log_path, index=False)

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
