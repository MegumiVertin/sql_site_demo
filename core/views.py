# core/views.py
import io
import zipfile
import tempfile
from pathlib import Path

import pandas as pd
from django.conf import settings
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt, require_GET
from django.core.cache import cache

from .tasks import run_translation  

if getattr(settings, "DEMO_MODE", False):
    from . import demo_logic as logic
else:
    from . import logic

FIXED_PROMPT = (
    "You are an assistant to translate the sql codes with the user message "
    "{SQL CODES: ...} into business documentation in plain English so that "
    "those without sql knowledge can understand.\n"
    "The sql codes are to support a customer marketing program at a "
    "supermarket chain.\n"
    "Summarize the codes to find out the objective, business rules, and "
    "execution steps.\n"
    "Export your output in the following format:\n"
    "{Objective ...}\n{Business Rules ...}\n{Execution Steps ...}\n"
    "It is critical for assistant to enclose Objective, Business Rules, "
    "Execution Steps within their own {} respectively, nothing outside {}."
)


def _table_html(xlsx: Path) -> str:
    df = pd.read_excel(xlsx)[["SQL_Index", "Type", "Content"]]
    df["Content"] = (
        df["Content"]
        .fillna("")
        .astype(str)
        .str.replace(r"\\n", "<br>", regex=True)
        .str.replace(r"\r?\n", "<br>", regex=True)
    )
    return df.to_html(index=False, border=1, classes="tbl", escape=False)


def _code_html(sql: str) -> str:
    lines = sql.rstrip().splitlines()
    pad = len(str(len(lines)))

    def esc(s: str) -> str:
        return (
            s.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

    body = "\n".join(f"{str(i + 1).rjust(pad)}  {esc(l)}" for i, l in enumerate(lines))
    return f'<pre class="code-block">{body}</pre>'


def index(request):
    return render(request, "index.html")


@csrf_exempt
def translate(request):
    if request.method != "POST":
        return HttpResponseBadRequest("POST only")

    sql_text = request.POST.get("sql_code", "").strip()
    sql_file = request.FILES.get("sql_file")

    if not sql_text and not sql_file:
        return HttpResponseBadRequest("sql_code or sql_file required")

    tmp_dir = Path(tempfile.mkdtemp())
    sql_xlsx = tmp_dir / "sql.xlsx"
    prm_xlsx = tmp_dir / "prompt.xlsx"

    if sql_file:
        raw = sql_file.read()
        sql_xlsx.write_bytes(raw)
        df_in = pd.read_excel(io.BytesIO(raw))
        sql_src = "\n".join(str(x) for x in df_in.iloc[:, 0])
    else:
        sql_src = sql_text
        pd.DataFrame([{"sql_code": sql_text}]).to_excel(sql_xlsx, index=False)

    rows = len(pd.read_excel(sql_xlsx))
    pd.DataFrame([{"prompt": FIXED_PROMPT}] * rows).to_excel(prm_xlsx, index=False)

    job = run_translation.delay(str(sql_xlsx), str(prm_xlsx), str(tmp_dir))
    cache.set(job.id, 0, 3600)

    return JsonResponse(
        {
            "job_id": job.id,
            "code_html": _code_html(sql_src),
            "html_trans": _table_html(sql_xlsx), 
        }
    )


@require_GET
def progress(request, job_id):
    pct = cache.get(job_id)
    if pct is None:
        return JsonResponse({"status": "unknown"}, status=404)

    if pct == 100:
        zip_url = f"/media/tmp/{job_id}.zip"
        return JsonResponse({"status": "done", "progress": 100, "zip_url": zip_url})

    return JsonResponse({"status": "running", "progress": pct})
