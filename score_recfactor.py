import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LATEST_RESULTS  = os.path.join(BASE_DIR, "datafiles", "latestresults", "latest-results.csv")
MC_TECHNICALS   = os.path.join(BASE_DIR, "datafiles", "mctechnicals", "mc_technicals.csv")
SCORE_REFACTOR  = os.path.join(BASE_DIR, "datafiles", "score_refactor", "score_refactor.csv")

def build_score_refactor(latest_results_path=LATEST_RESULTS, mc_technicals_path=MC_TECHNICALS, output_path=SCORE_REFACTOR):
    # -------- load --------
    lr = pd.read_csv(latest_results_path, low_memory=False)
    mt = pd.read_csv(mc_technicals_path, low_memory=False)

    # -------- normalization (column names only) --------
    lr.columns = [c.strip() for c in lr.columns]
    mt.columns = [c.strip() for c in mt.columns]

    # Helpful standard aliases (no value normalization, no dedup)
    rename_map = {
        "EPS latest quarter": "EPS latest quarter",
        "EPS preceding quarter": "EPS preceding quarter",
        "EPS preceding year quarter": "EPS preceding year quarter",
        "Return on equity": "Return on equity",
        "Return on capital employed": "Return on capital employed",
        "Price to Earning": "Price to Earning",
        "Industry PE": "Industry PE",
        "PEG Ratio": "PEG Ratio",
        "OPM latest quarter": "OPM latest quarter",
        "Public holding": "Public holding",
        "Return over 1week": "Return over 1week",
        "Return over 1month": "Return over 1month",
        "Return over 3months": "Return over 3months",
        "Return over 6months": "Return over 6months",
        "Name": "Name",
        "NSE Code": "NSE Code",
        "BSE Code": "BSE Code",
    }
    lr.rename(columns={k: v for k, v in rename_map.items() if k in lr.columns}, inplace=True)

    # Map variants -> mc essentials / mc technicals
    if "mc essentials" not in mt.columns:
        for alt in ["mc_essentials", "essentials", "MC Essentials", "MC_Essentials", "mcEssentials"]:
            if alt in mt.columns:
                mt.rename(columns={alt: "mc essentials"}, inplace=True)
                break
    if "mc technicals" not in mt.columns:
        for alt in ["mc_technicals", "technicals", "MC Technicals", "MC_Technicals", "mcTechnicals", "Technical Trend"]:
            if alt in mt.columns:
                mt.rename(columns={alt: "mc technicals"}, inplace=True)
                break

    # -------- FORCE exact Name-based LEFT join --------
    if "Name" not in lr.columns or "Name" not in mt.columns:
        raise ValueError("Exact-Name join requested, but 'Name' is missing in one of the files.")
    merge_key = "Name"

    mt_cols = [merge_key]
    if "mc essentials" in mt.columns: mt_cols.append("mc essentials")
    if "mc technicals" in mt.columns: mt_cols.append("mc technicals")

    df = lr.merge(mt[mt_cols], on=merge_key, how="left")  # LEFT join, keep all latest-results rows

    # -------- safe numeric --------
    def num(x, default=0.0):
        try:
            if isinstance(x, str):
                x = x.replace(",", "").replace("%", "").strip()
            v = float(x)
            if pd.isna(v):
                return float(default)
            return v
        except Exception:
            return float(default)

    # -------- scoring --------
    def score_eps(row):
        a = num(row.get("EPS latest quarter", 0))
        b = num(row.get("EPS preceding quarter", 0))
        c = num(row.get("EPS preceding year quarter", 0))
        return 20 if (a > b and a > c) else 0

    def score_roe_roce(row):
        roe  = num(row.get("Return on equity", 0))
        roce = num(row.get("Return on capital employed", 0))
        if roe > 20 and roce > 20: return 20
        if roe > 15 and roce > 15: return 10
        return 5

    def score_pe(row):
        pe  = num(row.get("Price to Earning", 0))
        ipe = num(row.get("Industry PE", 0))
        peg = num(row.get("PEG Ratio", 9e9))  # missing -> huge/unfavorable
        if pe < ipe and peg < 1: return 10
        if pe > ipe and peg < 1: return 10
        if pe < ipe and peg > 1: return 5
        return 0

    def score_mc(row):
        essentials = num(row.get("mc essentials", 0))
        technicals = str(row.get("mc technicals", "")).strip().lower()
        if essentials > 80 and technicals in ("bullish", "very bullish"): return 20
        if essentials > 80 and technicals == "neutral": return 5
        if essentials > 70 and technicals in ("bullish", "very bullish"): return 10
        return 0

    def score_opm(row):
        opm = num(row.get("OPM latest quarter", 0))
        if opm > 20: return 20
        if opm > 10: return 10
        return 5

    def score_public_holding(row):
        val = num(row.get("Public holding", 100))
        if val < 10: return 20
        if 10 <= val < 15: return 10
        if 15 <= val < 25: return 5
        return 0

    def score_returns(row):
        w1 = num(row.get("Return over 1week", 0))
        m1 = num(row.get("Return over 1month", 0))
        m3 = num(row.get("Return over 3months", 0))
        m6 = num(row.get("Return over 6months", 0))
        return 10 if (w1 > 0 and m1 > 10 and m3 > 10 and m6 > 10) else 0

    # -------- apply --------
    df["score_eps"]            = df.apply(score_eps, axis=1)
    df["score_pe"]             = df.apply(score_pe, axis=1)
    df["score_mc"]             = df.apply(score_mc, axis=1)
    df["score_opm"]            = df.apply(score_opm, axis=1)
    df["score_roe_roce"]       = df.apply(score_roe_roce, axis=1)
    df["score_public_holding"] = df.apply(score_public_holding, axis=1)
    df["score_returns"]        = df.apply(score_returns, axis=1)

    score_cols = [
        "score_eps","score_pe","score_mc","score_opm",
        "score_roe_roce","score_public_holding","score_returns"
    ]
    df["Total Score"] = df[score_cols].sum(axis=1)

    # -------- output (exclude MC columns) --------
    out_cols = [c for c in ["Name","NSE Code","BSE Code"] if c in df.columns] + score_cols + ["Total Score"]
    out = df[out_cols].copy()

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    out.to_csv(output_path, index=False)

    print(f"Input rows (latest-results): {len(lr)} | Output rows: {len(out)}")
    return out

if __name__ == "__main__":
    result = build_score_refactor()
    print(f"✅ Wrote: {SCORE_REFACTOR}  | rows: {len(result)}")
