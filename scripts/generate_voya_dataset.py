"""
generate_voya_dataset.py — Converts a VOYA Analytics CSV export to the
JavaScript dataset file consumed by voya-dashboard-v3.html.

Usage:
    python scripts/generate_voya_dataset.py \\
        --input  "analysis/data/VOYA Analytics Table Query.csv" \\
        --output docs/js/voya_backend_dataset_rebuilt.js

The output file defines a global `DATASET` array that the dashboard reads
immediately after the script tag loads.

Expected CSV columns (case-insensitive matching):
    session_id, start_time, end_time, duration_minutes,
    user_responses, bot_responses, resolution, channel, ...
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd


# Map CSV column names → JS field names
COLUMN_MAP = {
    "session_id":       "Session_ID",
    "start_time":       "Start_Time",
    "end_time":         "End_Time",
    "duration_minutes": "Duration_minutes",
    "user_responses":   "User_responses",
    "bot_responses":    "Bot_responses",
    "resolution":       "Resolution",
    "channel":          "Channel",
}

ENGAGED_THRESHOLD = 2  # user responses > N => "engaged user"


def load_csv(path: Path) -> pd.DataFrame:
    """Load and normalise the VOYA analytics CSV."""
    df = pd.read_csv(path)
    # Normalise column names to lowercase-underscore
    df.columns = [re.sub(r"\s+", "_", c.strip().lower()) for c in df.columns]
    return df


def transform(df: pd.DataFrame) -> list[dict]:
    """Convert DataFrame rows to DATASET record dicts."""
    records = []
    for _, row in df.iterrows():
        rec: dict = {}
        for csv_col, js_key in COLUMN_MAP.items():
            if csv_col in df.columns:
                val = row[csv_col]
                # Convert NaN to None
                rec[js_key] = None if pd.isna(val) else val
            else:
                rec[js_key] = None

        # Derived fields
        user_resp = rec.get("User_responses")
        try:
            resp_count = float(user_resp) if user_resp is not None else 0
        except (TypeError, ValueError):
            resp_count = 0

        rec["engaged_user"] = resp_count > ENGAGED_THRESHOLD
        rec["engagement_label"] = "engaged user" if rec["engaged_user"] else "not engaged"

        records.append(rec)

    return records


def write_js(records: list[dict], output_path: Path, source_name: str) -> None:
    """Write records to the JS dataset file."""
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    json_str = json.dumps(records, indent=None, default=str)

    js_content = f"""/* voya_backend_dataset_rebuilt.js
   Built from: {source_name}
   Generated: {now}
   Records: {len(records)}
   Flattened records for VOYA Insights dashboard.
   Note: engaged user string follows: User_responses > {ENGAGED_THRESHOLD} => "engaged user" else "not engaged"; engaged_user boolean mirrors this rule.
*/
var DATASET={json_str};
"""

    output_path.write_text(js_content, encoding="utf-8")
    size_mb = output_path.stat().st_size / 1_048_576
    print(f"✓ Written {len(records):,} records to {output_path} ({size_mb:.1f} MB)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert VOYA CSV export to dashboard JS dataset.")
    parser.add_argument(
        "--input", "-i",
        required=True,
        type=Path,
        help="Path to the VOYA analytics CSV file.",
    )
    parser.add_argument(
        "--output", "-o",
        default=Path("docs/js/voya_backend_dataset_rebuilt.js"),
        type=Path,
        help="Output JS file path (default: docs/js/voya_backend_dataset_rebuilt.js).",
    )
    args = parser.parse_args()

    if not args.input.exists():
        print(f"Error: input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    print(f"Loading {args.input} …")
    df = load_csv(args.input)
    print(f"  {len(df):,} rows, {len(df.columns)} columns")

    records = transform(df)
    write_js(records, args.output, source_name=args.input.name)


if __name__ == "__main__":
    main()
