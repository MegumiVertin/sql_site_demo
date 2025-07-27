# core/tasks.py
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

import pandas as pd
from celery import shared_task
from django.core.cache import cache

from . import logic


@shared_task(bind=True)
def run_translation(self, sql_xlsx: str, prm_xlsx: str, out_dir: str) -> None:
    job_id = self.request.id
    out = Path(out_dir)
    sql_df = pd.read_excel(sql_xlsx)
    prm_df = pd.read_excel(prm_xlsx)
    total = len(sql_df)

    trans_rows, eval_rows = [], []
    cum_line = 1

    for idx in range(total):
        sql_code = str(sql_df.at[idx, "sql_code"]).rstrip()
        prompt = str(prm_df.at[idx, "prompt"]).rstrip()

        ln_start = cum_line
        ln_total = len(sql_code.splitlines())
        cum_line += ln_total
        line_spec = f"(lines {ln_start}-{ln_start + ln_total - 1})"

        for temp in logic.ANT_TEMPS:
            user_prompt = f"{prompt}\n\nSQL Code:\n{sql_code}"
            system_msg = (
                "You are a helpful assistant that translates SQL into business "
                "documentation in plain English.\n"
                "{Objective: ...}\n{Business Rules: ...}\n{Execution Steps: ...}\n"
                f"Append the absolute SQL line range {line_spec} at the end of each brace."
            )

            try:
                ant_msg = logic.ant.messages.create(
                    model=logic.ANT_MODEL,
                    max_tokens=logic.ANT_MAX_TOKENS,
                    temperature=temp,
                    system=system_msg,
                    messages=[
                        {"role": "user",
                         "content": [{"type": "text", "text": user_prompt}]}
                    ],
                )
                text_out = ant_msg.content[0].text.strip()
            except Exception as e:
                text_out = f"[Translation Error] {e}"

            def grab(header: str) -> str:
                import re

                m = re.search(rf"\{{\s*{header}\s*:(.+?)\}}",
                              text_out, re.I | re.S)
                return m.group(1).strip() if m else ""

            base = {"SQL_Index": idx + 1, "Temperature": temp, "prompt": prompt}
            trans_rows.extend(
                [
                    {**base, "Type": "Objective", "Content": grab("Objective")},
                    {**base, "Type": "Business Rules", "Content": grab("Business Rules")},
                    {**base, "Type": "Execution Steps", "Content": grab("Execution Steps")},
                ]
            )

            eval_prompt = (
                "OUTPUT EXACTLY in this format:\n"
                "{ACCURACY: 0/1; Accuracy Confidence: n%; Explanation: ...}\n"
                "{CONCISENESS: 0/1; Conciseness Confidence: n%; Explanation: ...}\n"
                "{COMPLETENESS: 0/1; Completeness Confidence: n%; Explanation: ...}\n\n"
                f"Translation:\n\"\"\"{text_out}\"\"\""
            )
            try:
                eva = logic.oa.chat.completions.create(
                    model=logic.OA_MODEL,
                    temperature=0,
                    max_tokens=logic.OA_MAX_TOKENS,
                    messages=[
                        {"role": "system", "content": "You are a helpful evaluator."},
                        {"role": "user", "content": eval_prompt},
                    ],
                )
                raw_eval = eva.choices[0].message.content.strip()
            except Exception as e:
                raw_eval = f"[Evaluation Error] {e}"

            mets = logic._parse_eval_block(raw_eval)
            for off in range(3):
                eval_rows.append({**trans_rows[-3 + off], **mets})

        cache.set(job_id, int((idx + 1) / total * 100), 3600)

    out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(trans_rows).to_excel(out / "translation_results.xlsx", index=False)
    pd.DataFrame(eval_rows).to_excel(out / "analysis_results.xlsx", index=False)

    media_tmp = Path("media/tmp")
    media_tmp.mkdir(parents=True, exist_ok=True)
    zip_path = media_tmp / f"{job_id}.zip"
    with ZipFile(zip_path, "w", ZIP_DEFLATED) as zf:
        zf.write(out / "translation_results.xlsx", "translation.xlsx")
        zf.write(out / "analysis_results.xlsx", "analysis.xlsx")

    cache.set(job_id, 100, 3600)
