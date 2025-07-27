// static/app.js
// All comments in English, per requirement
document.addEventListener("DOMContentLoaded", () => {
  const txtSql      = document.getElementById("code");
  const codeBox     = document.getElementById("code-container");
  const inpFile     = document.getElementById("sql-file");
  const fileBadge   = document.getElementById("file-name");
  const btnUpload   = document.getElementById("btn-up");
  const btnRun      = document.getElementById("btn-run");
  const btnDownload = document.getElementById("btn-dl");
  const previewBox  = document.getElementById("preview");
  const bar         = document.getElementById("bar");         // <progress> element

  const refreshRun = () => {
    btnRun.disabled = !(inpFile.files.length || txtSql.value.trim());
  };

  // file picker
  btnUpload.addEventListener("click", () => inpFile.click());

  inpFile.addEventListener("change", () => {
    if (inpFile.files.length) {
      fileBadge.textContent   = `${inpFile.files[0].name} ✕`;
      fileBadge.style.display = "inline-block";
      txtSql.value            = "";
      txtSql.style.display    = "none";
    } else {
      fileBadge.style.display = "none";
      txtSql.style.display    = "block";
    }
    refreshRun();
  });

  fileBadge.addEventListener("click", () => {
    inpFile.value            = "";
    fileBadge.style.display  = "none";
    txtSql.style.display     = "block";
    refreshRun();
  });

  // textarea changes
  txtSql.addEventListener("input", () => {
    if (txtSql.value.trim()) {
      inpFile.value          = "";
      fileBadge.style.display = "none";
    }
    refreshRun();
  });

  // main run
  btnRun.addEventListener("click", async () => {
    const fd = new FormData();
    if (inpFile.files.length) {
      fd.append("sql_file", inpFile.files[0]);
    } else {
      fd.append("sql_code", txtSql.value.trim());
    }

    // UI state
    btnRun.disabled          = true;
    btnRun.textContent       = "Running…";
    previewBox.innerHTML     = '<p class="hint">Processing…</p>';
    btnDownload.classList.add("disabled");
    if (bar) {
      bar.value = 0;
      bar.removeAttribute("hidden");
    }

    try {
      // call new endpoint
      const res = await fetch("/api/translate/", { method: "POST", body: fd });
      if (!res.ok) throw new Error(await res.text());
      const j   = await res.json(); // {job_id, html_trans, code_html}

      // immediate preview
      previewBox.innerHTML = j.html_trans;
      codeBox.innerHTML    = j.code_html;

      // poll progress
      const poll = setInterval(async () => {
        const r2 = await fetch(`/api/progress/${j.job_id}/`);
        if (!r2.ok) return;                       // ignore transient errors
        const p = await r2.json();               // {status, progress, zip_url?}

        if (bar && p.progress !== undefined) bar.value = p.progress;

        if (p.status === "done") {
          clearInterval(poll);
          if (bar) bar.setAttribute("hidden", "true");

          btnDownload.href     = p.zip_url;
          btnDownload.download = p.zip_url.split("/").pop();
          btnDownload.classList.remove("disabled");
          btnRun.textContent = "Run";
          btnRun.disabled    = false;
        }
        if (p.status === "failed") {
          clearInterval(poll);
          throw new Error("Job failed on server");
        }
      }, 2000);
    } catch (e) {
      previewBox.innerHTML =
        `<pre style="color:red;white-space:pre-wrap">${e.message}</pre>`;
      if (bar) bar.setAttribute("hidden", "true");
      btnRun.textContent = "Run";
      btnRun.disabled    = false;
    }
  });

  refreshRun();
});
