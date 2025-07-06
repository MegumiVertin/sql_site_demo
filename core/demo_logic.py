# core/demo_logic.py
"""
Demo-mode logic:
    – Never calls external AI.
    – Re-uses pre-generated seed Excel files.
    – Simply truncates those seeds to match the number of SQL rows
      in the current user upload / input.
"""

import os
from pathlib import Path
import pandas as pd


# ─────────────────────────── seed files ────────────────────────────
SEED_DIR = Path(__file__).resolve().parent / "demo_seed"
SEED_TRANS = SEED_DIR / "seed_translation.xlsx"
SEED_ANAL  = SEED_DIR / "seed_analysis.xlsx"


def run_analysis(sql_path: str, prompt_path: str, output_dir: str):
    """
    Parameters
    ----------
    sql_path : str
        Temp *.xlsx* saved by the view – only used to know row count.
    prompt_path : str
        Unused here but kept for identical signature.
    output_dir : str
        Temp folder where the view expects translation_results.xlsx /
        analysis_results.xlsx.
    """
    # how many SQL rows did the user submit?
    n_rows = len(pd.read_excel(sql_path))

    # load seed results
    trans_df = pd.read_excel(SEED_TRANS)
    anal_df  = pd.read_excel(SEED_ANAL)

    # keep only rows whose SQL_Index ≤ n_rows
    trans_out = trans_df[trans_df["SQL_Index"] <= n_rows].copy()
    anal_out  = anal_df [anal_df ["SQL_Index"] <= n_rows].copy()

    # write to expected filenames
    os.makedirs(output_dir, exist_ok=True)
    trans_out.to_excel(Path(output_dir) / "translation_results.xlsx", index=False)
    anal_out .to_excel(Path(output_dir) / "analysis_results.xlsx",    index=False)
