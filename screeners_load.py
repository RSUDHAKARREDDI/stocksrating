import os
import pandas as pd
import operator as op

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_CSV  = os.path.join(BASE_DIR, "datafiles", "latestresults", "latest-results.csv")
OUTPUT_CSV = os.path.join(BASE_DIR, "datafiles", "latestresults", "latest-results_tagged.csv")

# -----------------------------
# Screener spec (structured)
# value can be: ("col", "<Other Column Name>") or ("const", <Number>)
# ops: ">", ">=", "<", "<=", "=", "!="
# -----------------------------
SCREENERS = {
    "EPS_PE_MSCAPS": [
        ("EPS latest quarter",       ">",  ("col",  "EPS preceding quarter")),
        ("EPS latest quarter",       ">",  ("col",  "EPS preceding year quarter")),
        ("EPS preceding quarter",    ">",  ("const", 0)),
        ("EPS latest quarter",       ">",  ("const", 0)),
        ("Price to Earning",         "<",  ("col",  "Industry PE")),
        ("Market Capitalization",    ">",  ("const", 1000)),
        ("Return over 1month",       ">",  ("const", 0)),
        ("Return over 3months",      ">",  ("const", 5)),
        ("Last result date",         "=",  ("const", 202509)),
        ("Promoter holding",         ">",  ("const", 70)),
        ("Market Capitalization",    "<",  ("const", 20000)),
    ],
"GOOD_ROE_ROCE_MORE_PE": [
        ("EPS latest quarter",       ">",  ("col",  "EPS preceding quarter")),
        ("EPS latest quarter",       ">",  ("col",  "EPS preceding year quarter")),
        ("Price to Earning",         "<",  ("col",  "Industry PE")),
        ("Promoter holding",         ">",  ("const", 50)),
        ("EPS latest quarter",       ">",  ("const", 2)),

        ("Market Capitalization",    ">",  ("const", 1000)),
        ("Return over 1month",       ">",  ("const", 0)),
        ("Return over 3months",      ">",  ("const", 5)),
        ("Last result date",         "=",  ("const", 202509)),

        ("Market Capitalization",    "<",  ("const", 20000)),
    ],
    # Add more screeners here (example):
    # "GOOD_ROE_ROCE_MORE_PE": [
    #     ("Return on equity", ">", ("const", 15)),
    #     ("Return on capital employed", ">", ("const", 15)),
    #     ("Price to Earning", ">", ("const", 10)),
    # ]
}

# Operator map
OPMAP = {
    ">":  op.gt,
    ">=": op.ge,
    "<":  op.lt,
    "<=": op.le,
    "=":  op.eq,
    "!=": op.ne,
}

# -----------------------------
# Load data
# -----------------------------
if not os.path.exists(INPUT_CSV):
    raise FileNotFoundError(f"File not found: {INPUT_CSV}")

df = pd.read_csv(INPUT_CSV)

# Coerce numeric columns (keep obvious text cols as-is)
TEXT_COLS = {"Name", "BSE Code", "NSE Code", "Industry"}
for c in df.columns:
    if c not in TEXT_COLS:
        df[c] = pd.to_numeric(df[c], errors="coerce")

# -----------------------------
# Evaluate screeners (vectorized)
# -----------------------------
def build_mask(df, conds):
    m = pd.Series(True, index=df.index)
    for col, op_str, val_spec in conds:
        if col not in df.columns:
            # Missing column -> fail whole condition set
            return pd.Series(False, index=df.index)
        if op_str not in OPMAP:
            raise ValueError(f"Unsupported operator: {op_str}")

        left = df[col]
        # Right side can be column or constant
        if val_spec[0] == "col":
            rhs_col = val_spec[1]
            if rhs_col not in df.columns:
                return pd.Series(False, index=df.index)
            right = df[rhs_col]
        elif val_spec[0] == "const":
            right = val_spec[1]
        else:
            raise ValueError(f"Bad value spec: {val_spec}")

        # Compare; NaNs will propagate to False with fillna(False)
        comp = OPMAP[op_str](left, right)
        m = m & comp.fillna(False)
    return m

matched_cols = []
for name, conditions in SCREENERS.items():
    mask = build_mask(df, conditions)
    df[name] = mask  # boolean column per screener
    matched_cols.append(name)

# Join all matched screener names for each row
def join_matches(row):
    hits = [s for s in matched_cols if bool(row.get(s))]
    return ", ".join(hits)

df["Matched_Screeners"] = df.apply(join_matches, axis=1)

# -----------------------------
# Save
# -----------------------------
os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
df.to_csv(OUTPUT_CSV, index=False)
print(f"✅ Processed {len(df)} rows")
print(f"📄 Tagged file: {OUTPUT_CSV}")

# Optional quick peek
preview_cols = [
    "Name", "Price to Earning", "Industry PE", "Market Capitalization",
    "Return over 1month", "Return over 3months", "Last result date",
    "Promoter holding", "EPS latest quarter", "EPS preceding quarter",
    "EPS preceding year quarter", "Matched_Screeners"
]
print(df[[c for c in preview_cols if c in df.columns]].head())


# --- Put this right after you define SCREENERS, OPMAP, load df, and coerce numerics ---

def condition_mask(df, left_col, op_str, val_spec):
    import operator as op
    OPMAP = {">":op.gt, ">=":op.ge, "<":op.lt, "<=":op.le, "=":op.eq, "!=":op.ne}

    if left_col not in df.columns or op_str not in OPMAP:
        return pd.Series(False, index=df.index)  # missing column or bad op

    left = df[left_col]
    if val_spec[0] == "col":
        rhs = df[val_spec[1]] if val_spec[1] in df.columns else pd.Series(pd.NA, index=df.index)
    elif val_spec[0] == "const":
        rhs = val_spec[1]
    else:
        return pd.Series(False, index=df.index)

    return OPMAP[op_str](left, rhs).fillna(False)

# Build debug columns: one per condition + final ALL column per screener
debug_cols = []
for screener_name, conds in SCREENERS.items():
    all_mask = pd.Series(True, index=df.index)
    for i, (col, op_str, val_spec) in enumerate(conds, start=1):
        dbg_col = f"{screener_name}__c{i}__{col} {op_str} {val_spec[0]}:{val_spec[1]}"
        m = condition_mask(df, col, op_str, val_spec)
        df[dbg_col] = m
        debug_cols.append(dbg_col)
        all_mask = all_mask & m
    df[screener_name] = all_mask
    debug_cols.append(screener_name)

# Matched list
match_cols = [s for s in SCREENERS.keys()]
df["Matched_Screeners"] = df.apply(lambda r: ", ".join([s for s in match_cols if bool(r.get(s))]), axis=1)

# Save a debug file with only useful columns up front
front = ["Name", "NSE Code", "Industry", "Price to Earning", "Industry PE",
         "Market Capitalization", "Return over 1month", "Return over 3months",
         "Last result date", "Promoter holding", "EPS latest quarter",
         "EPS preceding quarter", "EPS preceding year quarter", "Matched_Screeners"]
keep = [c for c in front if c in df.columns] + debug_cols
debug_out = os.path.join(BASE_DIR, "datafiles", "latestresults", "latest_results_tagged_debug.csv")
df[keep].to_csv(debug_out, index=False)
print(f"🔎 Debug file: {debug_out}")
