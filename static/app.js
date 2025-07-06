// static/app.js
document.addEventListener('DOMContentLoaded', () => {
  const txtSql      = document.getElementById('code');
  const codeBox     = document.getElementById('code-container');
  const inpFile     = document.getElementById('sql-file');
  const fileBadge   = document.getElementById('file-name');
  const btnUpload   = document.getElementById('btn-up');
  const btnRun      = document.getElementById('btn-run');
  const btnDownload = document.getElementById('btn-dl');
  const previewBox  = document.getElementById('preview');

  const refreshRun = () =>
    (btnRun.disabled = !(inpFile.files.length || txtSql.value.trim()));

  btnUpload.addEventListener('click', () => inpFile.click());

  inpFile.addEventListener('change', () => {
    if (inpFile.files.length) {
      fileBadge.textContent = `${inpFile.files[0].name} ✕`;
      fileBadge.style.display = 'inline-block';
      txtSql.value = '';
      txtSql.style.display = 'none';
    } else {
      fileBadge.style.display = 'none';
      txtSql.style.display = 'block';
    }
    refreshRun();
  });

  fileBadge.addEventListener('click', () => {
    inpFile.value = '';
    fileBadge.style.display = 'none';
    txtSql.style.display = 'block';
    refreshRun();
  });

  txtSql.addEventListener('input', () => {
    if (txtSql.value.trim()) {
      inpFile.value = '';
      fileBadge.style.display = 'none';
    }
    refreshRun();
  });

  btnRun.addEventListener('click', async () => {
    const fd = new FormData();
    if (inpFile.files.length) {
      fd.append('sql_file', inpFile.files[0]);
    } else {
      fd.append('sql_code', txtSql.value.trim());
    }

    btnRun.disabled = true;
    btnRun.textContent = 'Running…';
    previewBox.innerHTML = '<p class="hint">Processing…</p>';
    btnDownload.classList.add('disabled');

    try {
      const r = await fetch('/api/run/', { method: 'POST', body: fd });
      if (!r.ok) throw new Error(await r.text());
      const j = await r.json(); // {html_trans, code_html, zip_url}

      previewBox.innerHTML = j.html_trans;
      codeBox.innerHTML    = j.code_html;
      fileBadge.style.display = 'none';

      btnDownload.href     = j.zip_url;
      btnDownload.download = j.zip_url.split('/').pop();
      btnDownload.classList.remove('disabled');

    } catch (e) {
      previewBox.innerHTML =
        `<pre style="color:red;white-space:pre-wrap">${e.message}</pre>`;
    } finally {
      btnRun.disabled  = false;
      btnRun.textContent = 'Run';
    }
  });

  refreshRun();
});
