(function(){
  const $  = (s,p=document)=>p.querySelector(s);
  const $$ = (s,p=document)=>Array.from(p.querySelectorAll(s));

  const table = $("#resultsTable");
  if (!table) return;
  const tbody = table.tBodies[0];

  const idx = {
    name:0, bse:1, nse:2, industry:3, price:4, mcap_cap:5, mcap:6,
    eps_lq:7, eps_pq:8, eps_pyq:9, roe:10, roce:11,
    pe:12, indpe:13, pegr:14, debt:15, dbttoeq:16,
    promoter:17, fii:18, dii:19, pub:20,
    r1w:21, r1m:22, r3m:23, r6m:24,
    date:25, scr:26, ess:27, tech:28, margin:29, tscore:30,
    deliv:31, series:32, high52:33, low52:34
  };
// ----- Row Details Modal Logic -----
  const rowModal = $("#row_modal_backdrop");
  const rowModalBody = $("#row_modal_body");
  const rowModalTitle = $("#row_modal_title");

  if (tbody && rowModal) {
    tbody.addEventListener("click", (e) => {
      // Find the clicked row
      const tr = e.target.closest("tr");
      if (!tr || !tbody.contains(tr)) return;

      // Get headers to use as labels in the pop-up
      const headers = $$("#resultsTable thead th").map(th => th.textContent.trim());

      // Build the Key-Value table for the modal
      let html = '<table class="kv-table">';
      headers.forEach((h, i) => {
        const val = tr.children[i]?.textContent.trim() || "";
        const displayVal = val ? val : '<span style="opacity:0.5">(empty)</span>';
        html += `<tr><th>${h}</th><td>${displayVal}</td></tr>`;
      });
      html += '</table>';

      // Update and show the modal
      if (rowModalTitle) rowModalTitle.textContent = tr.children[idx.name].textContent;
      if (rowModalBody) rowModalBody.innerHTML = html;
      rowModal.style.display = "flex";
      document.body.classList.add("modal-open");
    });
  }

  // Close modal events
  $("#row_modal_close")?.addEventListener("click", () => {
    rowModal.style.display = "none";
    document.body.classList.remove("modal-open");
  });

  // Close on backdrop click
  rowModal?.addEventListener("click", (e) => {
    if (e.target === rowModal) {
      rowModal.style.display = "none";
      document.body.classList.remove("modal-open");
    }
  });
  // ----- Helper Functions -----
  function toNum(v){
    if(!v) return NaN;
    const s = v.replace(/[^\d.+\-eE]/g,'');
    return (!s || s==='+'||s==='-'||s==='.') ? NaN : parseFloat(s);
  }

  function getCell(tr, i){ return tr.children[i].textContent.trim(); }

  // ----- Sorting -----
  let sortState = { col: null, dir: 1 };
  $$("#resultsTable thead th").forEach((th, i) => {
    th.addEventListener("click", () => {
      const type = th.dataset.type || "text";
      sortState.dir = (sortState.col === i) ? -sortState.dir : 1;
      sortState.col = i;
      $$("#resultsTable thead th").forEach(h=>h.classList.remove("sort-asc","sort-desc"));
      th.classList.add(sortState.dir === 1 ? "sort-asc" : "sort-desc");
      const rows = $$("#resultsTable tbody tr");
      rows.sort((a,b)=> compare(getCell(a,i), getCell(b,i), type) * sortState.dir);
      rows.forEach(r=>tbody.appendChild(r));
    });
  });

  function compare(a,b,type){
    if(type==="num"){
      const x=toNum(a), y=toNum(b);
      return (isNaN(x) && isNaN(y)) ? 0 : isNaN(x) ? 1 : isNaN(y) ? -1 : x-y;
    }
    return (type==="date") ? new Date(a) - new Date(b) : a.localeCompare(b);
  }

  // ----- Filter UI Setup -----
  const F = {
    name: $("#f_name"), industryMulti: $("#f_industry_multi"),
    pe_min: $("#f_pe_min"), pe_max: $("#f_pe_max"),
    roe_min_r: $("#f_roe_min_r"), roe_hint: $("#f_roe_hint"),
    roce_min_r: $("#f_roce_min_r"), roce_hint: $("#f_roce_hint"),
    r1w_min_r: $("#f_r1w_min_r"), r1w_hint: $("#f_r1w_hint"),
    r1m_min_r: $("#f_r1m_min_r"), r1m_hint: $("#f_r1m_hint"),
    r3m_min_r: $("#f_r3m_min_r"), r3m_hint: $("#f_r3m_hint"),
    r6m_min_r: $("#f_r6m_min_r"), r6m_hint: $("#f_r6m_hint"),
    tscore_min_r: $("#f_tscore_min_r"), tscore_hint: $("#f_tscore_hint"),
    mcap_multi: $("#f_mcap_multi"), ess_min_r: $("#f_ess_min_r"), ess_hint: $("#f_ess_hint"),
    mc_tech_multi: $("#f_mc_tech_multi"), btn_reset: $("#btn_reset"),
  };

  function setupMinSlider(sliderEl, hintEl, colIdx){
    if(!sliderEl) return;
    let min = Infinity, max = -Infinity;
    $$("#resultsTable tbody tr").forEach(tr=>{
      const n = toNum(tr.children[colIdx].textContent);
      if(isFinite(n)){ if(n < min) min = n; if(n > max) max = n; }
    });
    if(min === Infinity) { min = 0; max = 100; }
    sliderEl.min = Math.floor(min); sliderEl.max = Math.ceil(max);
    sliderEl.value = sliderEl.min; sliderEl.dataset.active = "0";
    if(hintEl) hintEl.textContent = "All";

    sliderEl.addEventListener("input", ()=>{
      sliderEl.dataset.active = "1";
      if(hintEl) hintEl.textContent = `≥ ${sliderEl.value}`;
      applyFilters();
    });
  }

  // Init Sliders
  [
    [F.roe_min_r, F.roe_hint, idx.roe], [F.roce_min_r, F.roce_hint, idx.roce],
    [F.r1w_min_r, F.r1w_hint, idx.r1w], [F.r1m_min_r, F.r1m_hint, idx.r1m],
    [F.r3m_min_r, F.r3m_hint, idx.r3m], [F.r6m_min_r, F.r6m_hint, idx.r6m],
    [F.tscore_min_r, F.tscore_hint, idx.tscore], [F.ess_min_r, F.ess_hint, idx.ess]
  ].forEach(args => setupMinSlider(...args));

  function gteActive(slider, val){
    if(!slider || slider.dataset.active !== "1") return true;
    const n = toNum(val); return isFinite(n) && n >= parseFloat(slider.value);
  }

  function applyFilters(){
    const indS = new Set(selectedValues(F.industryMulti)), mcapS = new Set(selectedValues(F.mcap_multi)), techS = new Set(selectedValues(F.mc_tech_multi));

    $$("#resultsTable tbody tr").forEach(tr=>{
      const c = tr.children;
      const peV = toNum(c[idx.pe].textContent);
      const peMin = F.pe_min.value ? parseFloat(F.pe_min.value) : -Infinity;
      const peMax = F.pe_max.value ? parseFloat(F.pe_max.value) : Infinity;

      const ok = (!F.name.value || c[idx.name].textContent.toLowerCase().includes(F.name.value.toLowerCase())) &&
                 (indS.size === 0 || indS.has(c[idx.industry].textContent.toLowerCase())) &&
                 (mcapS.size === 0 || mcapS.has(c[idx.mcap].textContent.toLowerCase())) &&
                 (techS.size === 0 || techS.has(c[idx.tech].textContent.toLowerCase())) &&
                 (peV >= peMin && peV <= peMax) &&
                 gteActive(F.roe_min_r, c[idx.roe].textContent) &&
                 gteActive(F.roce_min_r, c[idx.roce].textContent) &&
                 gteActive(F.r1w_min_r, c[idx.r1w].textContent) &&
                 gteActive(F.r1m_min_r, c[idx.r1m].textContent) &&
                 gteActive(F.r3m_min_r, c[idx.r3m].textContent) &&
                 gteActive(F.r6m_min_r, c[idx.r6m].textContent) &&
                 gteActive(F.tscore_min_r, c[idx.tscore].textContent) &&
                 gteActive(F.ess_min_r, c[idx.ess].textContent);

      tr.style.display = ok ? "" : "none";
    });
    applyHighlights();
  }

  // ----- Highlighting Logic -----
  function applyHighlights(){
    $$("#resultsTable tbody tr").forEach(tr=>{
      if(tr.style.display === "none") return;
      const c = tr.children;
      [idx.eps_lq, idx.pe, idx.roe, idx.tscore, idx.deliv].forEach(i => {
          const td = c[i];
          const val = toNum(td.textContent);
          td.classList.remove("bg-good", "bg-bad");
          if(i === idx.tscore && val >= 70) td.classList.add("bg-good");
          if(i === idx.deliv && val > 60) td.classList.add("bg-good");
      });
    });
  }

  function selectedValues(el){ return Array.from(el?.selectedOptions || []).map(o=>o.value.toLowerCase()); }

  // ----- Events -----
  const debounce = (fn, ms) => { let t; return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), ms); }; };
  [F.name, F.pe_min, F.pe_max].forEach(el => el.addEventListener("input", debounce(applyFilters, 150)));
  [F.industryMulti, F.mcap_multi, F.mc_tech_multi].forEach(el => el.addEventListener("change", applyFilters));

  $("#btn_reset").addEventListener("click", () => location.reload());
  $("#btn_toggle_filters").addEventListener('click', () => $(".page-wrap").classList.toggle('filters-offcanvas'));
  $("#btn_filters_handle").addEventListener('click', () => $(".page-wrap").classList.remove('filters-offcanvas'));

  // ----- Initializers -----
  function fillMulti(el, col){
    const vals = new Set(); $$("#resultsTable tbody tr").forEach(tr=>vals.add(tr.children[col].textContent.trim()));
    Array.from(vals).sort().forEach(v=>{ const o = new Option(v,v); el.add(o); });
  }
  fillMulti(F.industryMulti, idx.industry); fillMulti(F.mcap_multi, idx.mcap); fillMulti(F.mc_tech_multi, idx.tech);

  // Logic for 52-week distances
  $$('.dist-container').forEach(container => {
      const p = parseFloat(container.dataset.price), h = parseFloat(container.dataset.high), l = parseFloat(container.dataset.low);
      if(p && h) container.querySelector('.dist-high').textContent = `${((p-h)/h*100).toFixed(1)}% from High`;
      if(p && l) container.querySelector('.dist-low').textContent = `+${((p-l)/l*100).toFixed(1)}% from Low`;
  });

  applyFilters();
})();