#!/usr/bin/env python3
"""
check_active_ipos_v4.py
-----------------------
Purpose:
- Read a Jay Ritter-style IPO Excel (e.g., "IPO-age.xlsx"), filter IPOs since a given date.
- Classify each ticker as ACTIVE/INACTIVE using a *light* Yahoo Finance probe
  (daily/weekly heartbeat, no bulk data download).
- Attach IPO date to outputs.
- Be resilient to Yahoo rate limiting via retries and exponential backoff.
- Cache results to skip previously-checked tickers across runs.
- Gracefully resume after interruption.

Outputs (in --outdir):
  - active_ipos_since_<YYYY-MM-DD>.csv
  - inactive_or_delisted_ipos_since_<YYYY-MM-DD>.csv
  - ipo_activity_check_log_since_<YYYY-MM-DD>.csv
  - cache_active_status_since_<YYYY-MM-DD>.csv  (internal cache you can reuse/resume)

Usage examples:
  python3 check_active_ipos_v4.py --input IPO-age.xlsx --sheet "1975-2024" --since 2015-01-01 --freq weekly --outdir . --verbose
  python3 check_active_ipos_v4.py --input IPO-age.xlsx --sheet "1975-2024" --since 2000-01-01 --freq daily  --outdir . --verbose --sleep 0.5

Notes:
- "Active" means Yahoo returns *some* recent OHLC or metadata indicating a live quote.
- Heuristic only. For research-grade results, validate with CRSP or exchange master files.
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
    ap.add_argument("--sleep", type=float, default=0.4, help="Base seconds to sleep between API calls")
    ap.add_argument("--max", type=int, default=None, help="Optional cap on number of tickers to check (for testing)")
    ap.add_argument("--verbose", action="store_true", help="Print progress information")
    ap.add_argument("--max-retries", type=int, default=6, help="Max retries on rate-limit or transient errors")
    ap.add_argument("--checkpoint-every", type=int, default=50, help="Write cache/log every N tickers")
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
    tk = yf_mod.Ticker(ticker)
    if freq == "weekly":
        hist = tk.history(period="3mo", interval="1wk", auto_adjust=False, actions=False)
    else:
        hist = tk.history(period="5d", interval="1d", auto_adjust=False, actions=False)

    if hist is not None and not hist.empty and "Close" in hist.columns and hist["Close"].notna().any():
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

def classify_with_retries(ticker, yf_mod, freq, base_sleep, max_retries, verbose=False):
    """
    Calls is_active_yf_light with exponential backoff on rate-limit/transient errors.
    Returns (active: bool, note: str)
    """
    attempt = 0
    while True:
        try:
            active, note = is_active_yf_light(ticker, yf_mod, freq=freq)
            return active, note
        except Exception as e:
            msg = str(e)
            ratelimited = ("YFRateLimitError" in msg) or ("Too Many Requests" in msg) or ("429" in msg)
            transient = ratelimited or ("timed out" in msg.lower()) or ("network" in msg.lower())

            if not transient or attempt >= max_retries:
                if verbose:
                    print(f"[WARN] {ticker}: giving up after {attempt} retries ({msg})", file=sys.stderr)
                return False, f"error:{type(e).__name__}"
            # backoff
            sleep_s = base_sleep * (2 ** attempt)
            if verbose:
                print(f"[INFO] {ticker}: transient error '{msg}'. Sleeping {sleep_s:.1f}s (attempt {attempt+1}/{max_retries})", file=sys.stderr)
            time.sleep(sleep_s)
            attempt += 1

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

    # Load IPOs
    ipo = load_ipos(args.input, args.sheet, args.since, verbose=args.verbose)

    since_tag = pd.to_datetime(args.since).date().isoformat()
    cache_path = os.path.join(args.outdir, f"cache_active_status_since_{since_tag}.csv")

    # Load cache if present
    cache = None
    if os.path.exists(cache_path):
        cache = pd.read_csv(cache_path)
        if args.verbose:
            print(f"[INFO] Loaded cache: {cache_path} ({len(cache)} rows)", file=sys.stderr)

    # Prepare list to check
    to_check = ipo[["Ticker", "IPO name", "offer date"]].copy()
    to_check.rename(columns={"IPO name": "Company", "offer date": "IPO_Date"}, inplace=True)

    # Merge with cache to skip already-checked
    if cache is not None and not cache.empty:
        merged = to_check.merge(cache[["Ticker", "Active", "Check_Note"]], on="Ticker", how="left", suffixes=("", "_cached"))
    else:
        merged = to_check.copy()
        merged["Active"] = pd.NA
        merged["Check_Note"] = pd.NA

    # Optional cap
    if args.max is not None:
        merged = merged.iloc[: args.max].copy()

    results = []
    checked = 0
    start = time.time()

    try:
        for idx, row in merged.iterrows():
            tkr = row["Ticker"]
            comp = row["Company"]
            dte = row["IPO_Date"]

            if pd.notna(row["Active"]):
                # Already cached
                active = bool(row["Active"])
                note = str(row["Check_Note"])
                status = "CACHED"
            else:
                active, note = classify_with_retries(tkr, yf, args.freq, args.sleep, args.max_retries, verbose=args.verbose)
                status = "FRESH"

            results.append({
                "Ticker": tkr,
                "Company": comp,
                "IPO_Date": pd.to_datetime(dte).date() if not pd.isna(dte) else dte,
                "Active": bool(active),
                "Check_Note": note,
            })

            checked += 1
            if args.verbose:
                print(f"[{checked}/{len(merged)}] {tkr:10s} -> {'ACTIVE' if active else 'INACTIVE'} ({note}) [{status}]", file=sys.stderr)

            # Periodic checkpoint
            if checked % args.checkpoint_every == 0:
                out_df = pd.DataFrame(results)
                # Append to/refresh cache
                cache_df = out_df[["Ticker", "Active", "Check_Note"]].drop_duplicates("Ticker")
                cache_df.to_csv(cache_path, index=False)
                if args.verbose:
                    print(f"[INFO] Checkpoint saved cache: {cache_path} (rows so far: {len(cache_df)})", file=sys.stderr)
                time.sleep(args.sleep)

            # polite base sleep between calls when not cached
            if status == "FRESH":
                time.sleep(args.sleep)

    except KeyboardInterrupt:
        print("\n[INFO] Interrupted by user. Saving partial results...", file=sys.stderr)

    # Finalize outputs
    out = pd.DataFrame(results)
    if out.empty:
        print("[WARN] No results to save. Did caching skip everything? Try deleting the cache or changing --since/--max.", file=sys.stderr)
        return

    # Split & save (keep IPO_Date attached)
    active_df = out[out["Active"]][["Ticker", "Company", "IPO_Date"]].sort_values(["IPO_Date", "Ticker"]).reset_index(drop=True)
    inactive_df = out[~out["Active"]][["Ticker", "Company", "IPO_Date"]].sort_values(["IPO_Date", "Ticker"]).reset_index(drop=True)

    active_path = os.path.join(args.outdir, f"active_ipos_since_{since_tag}.csv")
    inactive_path = os.path.join(args.outdir, f"inactive_or_delisted_ipos_since_{since_tag}.csv")
    log_path = os.path.join(args.outdir, f"ipo_activity_check_log_since_{since_tag}.csv")

    active_df.to_csv(active_path, index=False)
    inactive_df.to_csv(inactive_path, index=False)
    out.to_csv(log_path, index=False)

    # Update cache with all results
    cache_df = out[["Ticker", "Active", "Check_Note"]].drop_duplicates("Ticker")
    cache_df.to_csv(cache_path, index=False)

    print(f"[DONE] Saved files to: {os.path.abspath(args.outdir)}")
    print(f"  ACTIVE  -> {active_path}  (rows={len(active_df)})")
    print(f"  INACTIVE-> {inactive_path} (rows={len(inactive_df)})")
    print(f"  LOG     -> {log_path}      (rows={len(out)})")
    print(f"  CACHE   -> {cache_path}    (rows={len(cache_df)})")

    try:
        files = sorted(os.listdir(args.outdir))
        print("\n[DIR LIST]")
        for f in files:
            print(" ", f)
    except Exception:
        pass

if __name__ == "__main__":
    main()
