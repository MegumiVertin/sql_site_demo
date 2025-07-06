# core/logic.py
import os, re, time, pandas as pd
from anthropic import Anthropic
from openai import OpenAI

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
OPENAI_API_KEY    = os.getenv("OPENAI_API_KEY")

ANT_MODEL      = "claude-3-7-sonnet-20250219"
OA_MODEL       = "gpt-4o"
ANT_TEMPS      = [0.1]
ANT_MAX_TOKENS = 4096
OA_MAX_TOKENS  = 512

ant = Anthropic(api_key=ANTHROPIC_API_KEY)
oa  = OpenAI   (api_key=OPENAI_API_KEY)


def _parse_eval_block(text: str) -> dict:
    mkeys = ["Accurate", "Accurate Confidence (%)", "Accurate Explanation",
             "Concise",  "Concise Confidence (%)",  "Concise Explanation",
             "Complete", "Complete Confidence (%)", "Complete Explanation"]
    out = {k: None for k in mkeys}

    for blk in re.findall(r"\{([^}]*)\}", text.replace("}\n{", "}|{")):
        val  = re.search(r"\b([01])\b", blk)
        conf = re.search(r"(\d+)%", blk)
        expl = re.search(r"Explanation\s*:\s*(.+)", blk, re.I)
        key  = blk.split(':', 1)[0].strip().lower()
        if key.startswith("accur"):
            out.update({
                "Accurate": val.group(1) if val else None,
                "Accurate Confidence (%)": conf.group(1) if conf else None,
                "Accurate Explanation": expl.group(1).strip() if expl else None})
        elif key.startswith("concise"):
            out.update({
                "Concise": val.group(1) if val else None,
                "Concise Confidence (%)": conf.group(1) if conf else None,
                "Concise Explanation": expl.group(1).strip() if expl else None})
        elif key.startswith("complete"):
            out.update({
                "Complete": val.group(1) if val else None,
                "Complete Confidence (%)": conf.group(1) if conf else None,
                "Complete Explanation": expl.group(1).strip() if expl else None})
    return out


def run_analysis(sql_path: str, prompt_path: str, out_dir: str):
    sql_df    = pd.read_excel(sql_path)
    prompt_df = pd.read_excel(prompt_path)
    if len(sql_df) != len(prompt_df):
        raise ValueError("SQL and Prompt files must have the same number of rows")

    trans_rows, eval_rows = [], []
    cum_line = 1

    for idx in range(len(sql_df)):
        sql_code  = str(sql_df.at[idx, "sql_code"]).rstrip()
        prompt    = str(prompt_df.at[idx, "prompt"]).rstrip()

        ln_start  = cum_line
        ln_total  = len(sql_code.splitlines())
        cum_line += ln_total
        line_spec = f"(lines {ln_start}-{ln_start + ln_total - 1})"

        for temp in ANT_TEMPS:
            user_prompt = f"{prompt}\n\nSQL Code:\n{sql_code}"
            system_msg  = (
                "You are a helpful assistant that translates SQL into business "
                "documentation in plain English.\n"
                "Output EXACTLY in this format (include the braces):\n"
                "{Objective: ...}\n{Business Rules: ...}\n{Execution Steps: ...}\n"
                "At the very end of the text inside each pair of braces, append "
                f"the absolute SQL line range {line_spec} without changing any "
                "other punctuation or line breaks."
            )

            try:
                ant_msg = ant.messages.create(
                    model=ANT_MODEL,
                    max_tokens=ANT_MAX_TOKENS,
                    temperature=temp,
                    system=system_msg,
                    messages=[{"role": "user",
                               "content": [{"type": "text", "text": user_prompt}]}])
                text_out = ant_msg.content[0].text.strip()
            except Exception as e:
                text_out = f"[Translation Error] {e}"

            def grab(h):
                m = re.search(rf"\{{\s*{h}\s*:(.+?)\}}", text_out, re.I | re.S)
                return m.group(1).strip() if m else ""

            base = {"SQL_Index": idx + 1, "Temperature": temp, "prompt": prompt}
            trans_rows += [
                {**base, "Type": "Objective",       "Content": grab("Objective")},
                {**base, "Type": "Business Rules",  "Content": grab("Business Rules")},
                {**base, "Type": "Execution Steps", "Content": grab("Execution Steps")},
            ]

            eval_prompt = (
                "OUTPUT EXACTLY in this format:\n"
                "{ACCURACY: 0/1; Accuracy Confidence: n%; Explanation: ...}\n"
                "{CONCISENESS: 0/1; Conciseness Confidence: n%; Explanation: ...}\n"
                "{COMPLETENESS: 0/1; Completeness Confidence: n%; Explanation: ...}\n\n"
                f"Translation:\n\"\"\"{text_out}\"\"\""
            )
            try:
                eva = oa.chat.completions.create(
                    model=OA_MODEL,
                    temperature=0,
                    max_tokens=OA_MAX_TOKENS,
                    messages=[{"role": "system", "content": "You are a helpful evaluator."},
                              {"role": "user",   "content": eval_prompt}])
                raw_eval = eva.choices[0].message.content.strip()
            except Exception as e:
                raw_eval = f"[Evaluation Error] {e}"

            mets = _parse_eval_block(raw_eval)
            for off in range(3):
                eval_rows.append({**trans_rows[-3 + off], **mets})

            time.sleep(0.5)

    os.makedirs(out_dir, exist_ok=True)
    pd.DataFrame(trans_rows).to_excel(os.path.join(out_dir, "translation_results.xlsx"), index=False)
    pd.DataFrame(eval_rows ).to_excel(os.path.join(out_dir, "analysis_results.xlsx"),    index=False)
