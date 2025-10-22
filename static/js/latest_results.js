// copy of quality_stocks.js with just a different storage key suffix
// (Everything else is identical if your columns match)

(function(){
  const $  = (s,p=document)=>p.querySelector(s);
  const $$ = (s,p=document)=>Array.from(p.querySelectorAll(s));

  const table = $("#resultsTable");
  if (!table) return;
  const tbody = table.tBodies[0];

  // ... [identical helpers: sort, toNum, compare] ...

  let sortState = { col: null, dir: 1 };
  $$("#resultsTable thead th").forEach((th, idx) => {
    th.addEventListener("click", () => {
      const type = th.dataset.type || "text";
      sortState.dir = (sortState.col === idx) ? -sortState.dir : 1;
      sortState.col = idx;
      $$("#resultsTable thead th").forEach(h=>h.classList.remove("sort-asc","sort-desc"));
      th.classList.add(sortState.dir === 1 ? "sort-asc" : "sort-desc");
      const rows = $$("#resultsTable tbody tr");
      rows.sort((a,b)=> compare(getCell(a,idx), getCell(b,idx), type) * sortState.dir);
      rows.forEach(r=>tbody.appendChild(r));
      applyHighlights();
    });
  });

  function getCell(tr, idx){ return tr.children[idx].textContent.trim(); }
  function toNum(v){ if(!v) return NaN; const s=v.replace(/[^\d.+\-eE]/g,''); if(!s||s==='+'||s==='-'||s==='.') return NaN; return parseFloat(s); }
  function compare(a,b,type){
    if(type==="num"){ const x=toNum(a),y=toNum(b); if(isNaN(x)&&isNaN(y)) return 0; if(isNaN(x)) return 1; if(isNaN(y)) return -1; return x-y; }
    if(type==="date"){ return new Date(a)-new Date(b); }
    return a.localeCompare(b, undefined, {sensitivity:"base"});
  }

  const F = {
    name: $("#f_name"),
    industryMulti: $("#f_industry_multi"),
    pe_min: $("#f_pe_min"),
    pe_max: $("#f_pe_max"),
    roe_min_r:  $("#f_roe_min_r"), roe_hint: $("#f_roe_hint"),
    roce_min_r: $("#f_roce_min_r"), roce_hint: $("#f_roce_hint"),
    ess_min_r:  $("#f_ess_min_r"),  ess_hint: $("#f_ess_hint"),
    mcap_multi: $("#f_mcap_multi"),
    mc_tech_multi: $("#f_mc_tech_multi"),
    btn_reset: $("#btn_reset"),
  };

  const idx = {
    name:0, bse:1, nse:2, industry:3,
    price:4, mcap_capitalization:5, mcap:6,
    eps_lq:7, eps_pq:8, eps_pyq:9,
    roe:10, roce:11,
    pe:12, indpe:13, pegr:14,
    debt:15, dbttoeq:16,
    promoter:17, fii:18, dii:19, pub:20,
    r1w:21, r1m:22, r3m:23, r6m:24,
    date:25, scr:26, ess:27, tech:28, margin:29,tscore:30
  };

  function applyHighlights(){
    const rows = $$("#resultsTable tbody tr");
    rows.forEach(tr=>{
      const c = tr.children;
      for (const td of c) td.classList.remove("bg-good","bg-bad");

      const eps_lq  = toNum(c[idx.eps_lq].textContent);
      const eps_pq  = toNum(c[idx.eps_pq].textContent);
      const eps_pyq = toNum(c[idx.eps_pyq].textContent);
      if ([eps_lq,eps_pq,eps_pyq].every(Number.isFinite)) {
        const ok = (eps_lq > eps_pq) && (eps_lq > eps_pyq);
        [c[idx.eps_lq], c[idx.eps_pq], c[idx.eps_pyq]].forEach(td => td.classList.add(ok ? "bg-good" : "bg-bad"));
      }

      const pe   = toNum(c[idx.pe].textContent);
      const indp = toNum(c[idx.indpe].textContent);
      if ([pe,indp].every(Number.isFinite)) {
        const ok = pe < indp;
        [c[idx.pe], c[idx.indpe]].forEach(td => td.classList.add(ok ? "bg-good" : "bg-bad"));
      }

      const r1w = toNum(c[idx.r1w].textContent);
      const r1m = toNum(c[idx.r1m].textContent);
      const r3m = toNum(c[idx.r3m].textContent);
      const r6m = toNum(c[idx.r6m].textContent);
      if ([r1w,r1m,r3m,r6m].every(Number.isFinite)) {
        const ok = (r1w > 0) && (r1m > 10) && (r3m > 10) && (r6m > 0);
        [c[idx.r1w], c[idx.r1m], c[idx.r3m], c[idx.r6m]].forEach(td => td.classList.add(ok ? "bg-good" : "bg-bad"));
      }

      const roe  = toNum(c[idx.roe].textContent);
      const roce = toNum(c[idx.roce].textContent);
      if ([roe,roce].every(Number.isFinite)) {
        const ok = (roe > 15) && (roce > 15);
        [c[idx.roe], c[idx.roce]].forEach(td => td.classList.add(ok ? "bg-good" : "bg-bad"));
      }

      const pegr = toNum(c[idx.pegr].textContent);
      if (Number.isFinite(pegr)) c[idx.pegr].classList.add(pegr < 1 ? "bg-good" : "bg-bad");

      const dte = toNum(c[idx.dbttoeq].textContent);
      if (Number.isFinite(dte)) c[idx.dbttoeq].classList.add(dte < 1 ? "bg-good" : "bg-bad");

      const pub = toNum(c[idx.pub].textContent);
      if (Number.isFinite(pub)) c[idx.pub].classList.add(pub < 25 ? "bg-good" : "bg-bad");

      // 8) Total Score < 25
      const tscore = toNum(c[idx.tscore].textContent);
      if (Number.isFinite(tscore)) {
        c[idx.tscore].classList.add(tscore >= 70 ? "bg-good" : "bg-bad");
      }
    });
  }

  function fillMultiSelect(selectEl, values){
    if(!selectEl) return;
    selectEl.innerHTML = "";
    values.sort((a,b)=>a.localeCompare(b, undefined, {sensitivity:"base"}))
      .forEach(v=>{
        const opt = document.createElement("option");
        opt.value = opt.textContent = v;
        selectEl.appendChild(opt);
      });
  }
  function uniqueColumnValues(colIndex){
    const set = new Set();
    $$("#resultsTable tbody tr").forEach(tr=>{
      const val = tr.children[colIndex].textContent.trim();
      if(val) set.add(val);
    });
    return Array.from(set);
  }
  fillMultiSelect(F.industryMulti, uniqueColumnValues(idx.industry));
  fillMultiSelect(F.mc_tech_multi, uniqueColumnValues(idx.tech));
  fillMultiSelect(F.mcap_multi,    uniqueColumnValues(idx.mcap));

  function colMinMax(colIndex){
    let min = +Infinity, max = -Infinity;
    $$("#resultsTable tbody tr").forEach(tr=>{
      const n = toNum(tr.children[colIndex].textContent);
      if(isFinite(n)){ if(n < min) min = n; if(n > max) max = n; }
    });
    if(min === +Infinity) min = 0;
    if(max === -Infinity) max = 0;
    return {min, max};
  }
  function setupMinSlider(sliderEl, hintEl, colIndex){
    if(!sliderEl) return;
    const {min, max} = colMinMax(colIndex);
    const span = Math.max(1, max - min);
    let step = Math.pow(10, Math.floor(Math.log10(span)) - 2);
    if(!isFinite(step) || step <= 0) step = 1;

    sliderEl.min = String(Math.floor(min));
    sliderEl.max = String(Math.ceil(max));
    sliderEl.step = String(step);
    sliderEl.value = String(Math.floor(min));

    sliderEl.dataset.active = "0";
    if(hintEl) hintEl.textContent = "All";

    sliderEl.addEventListener("input", ()=>{
      sliderEl.dataset.active = "1";
      if(hintEl) hintEl.textContent = `≥ ${sliderEl.value}`;
      applyFilters();
    });
  }
  setupMinSlider(F.roe_min_r,  F.roe_hint,  idx.roe);
  setupMinSlider(F.roce_min_r, F.roce_hint, idx.roce);
  setupMinSlider(F.ess_min_r,  F.ess_hint,  idx.ess);

  function debounce(fn, ms){ let t; return (...args)=>{ clearTimeout(t); t=setTimeout(()=>fn.apply(this,args), ms); }; }
  function selectedValues(selectEl){ return Array.from((selectEl?.selectedOptions)||[]).map(o=>o.value.toLowerCase()); }
  function matchesText(value, needle){ if(!needle) return true; return value.toLowerCase().includes((needle||"").toLowerCase()); }
  function gteIfActive(sliderEl, cellText){ if(!sliderEl || sliderEl.dataset.active !== "1") return true; const v=toNum(cellText); if(!isFinite(v)) return false; return v >= parseFloat(sliderEl.value); }
  function betweenNum(val, min, max){ const v=toNum(val); if(!isFinite(v)) return false; if(min!==""&&isFinite(min)&&v<parseFloat(min))return false; if(max!==""&&isFinite(max)&&v>parseFloat(max))return false; return true; }

  const baseInputs = [F.name, F.industryMulti, F.mcap_multi, F.mc_tech_multi, F.pe_min, F.pe_max].filter(Boolean);
  baseInputs.forEach(el=>{ const evt = (el.tagName === "SELECT") ? "change" : "input"; el.addEventListener(evt, debounce(applyFilters, 120)); });
  F.btn_reset && F.btn_reset.addEventListener("click", resetFilters);

  function applyFilters(){
    const indSel  = new Set(selectedValues(F.industryMulti));
    const mcapSel = new Set(selectedValues(F.mcap_multi));
    const techSel = new Set(selectedValues(F.mc_tech_multi));

    $$("#resultsTable tbody tr").forEach(tr=>{
      const c = tr.children;

      const nameOk = matchesText(c[idx.name].textContent, F.name?.value);

      const indVal = c[idx.industry].textContent.trim().toLowerCase();
      const industryOk = indSel.size === 0 || indSel.has(indVal);

      const peOk = (()=>{
        const min = F.pe_min?.value === "" ? -Infinity : parseFloat(F.pe_min.value);
        const max = F.pe_max?.value === "" ? +Infinity : parseFloat(F.pe_max.value);
        return betweenNum(c[idx.pe].textContent, min, max);
      })();

      const roeOk  = gteIfActive(F.roe_min_r,  c[idx.roe].textContent);
      const roceOk = gteIfActive(F.roce_min_r, c[idx.roce].textContent);
      const essOk  = gteIfActive(F.ess_min_r,  c[idx.ess].textContent);

      const mcapVal = c[idx.mcap].textContent.trim().toLowerCase();
      const mcapOk  = mcapSel.size === 0 || mcapSel.has(mcapVal);

      const techVal = c[idx.tech].textContent.trim().toLowerCase();
      const techOk  = techSel.size === 0 || techSel.has(techVal);

      const ok = nameOk && industryOk && peOk && roeOk && roceOk && essOk && mcapOk && techOk;
      tr.style.display = ok ? "" : "none";
    });

    applyHighlights();
  }

  function resetFilters(){
    [F.name, F.pe_min, F.pe_max].forEach(el => { if(el) el.value = ""; });
    [F.industryMulti, F.mcap_multi, F.mc_tech_multi].forEach(sel=>{
      if(!sel) return; Array.from(sel.options).forEach(o=>o.selected = false);
    });

    setupMinSlider(F.roe_min_r,  F.roe_hint,  idx.roe);
    setupMinSlider(F.roce_min_r, F.roce_hint, idx.roce);
    setupMinSlider(F.ess_min_r,  F.ess_hint,  idx.ess);

    applyFilters();
  }

  // init
  applyFilters(); applyHighlights();

  // Pie modal
  const modal = $("#modal_backdrop");
  const btnPie = $("#btn_industry_pie");
  const btnClose = $("#modal_close");
  const canvas = $("#industry_pie");
  const legend = $("#industry_legend");
  function openModal(){ if(!modal) return; modal.style.display = "flex"; }
  function closeModal(){ if(!modal) return; modal.style.display = "none"; }
  btnPie && btnPie.addEventListener("click", ()=>{ renderIndustryPie(); openModal(); });
  btnClose && btnClose.addEventListener("click", closeModal);
  modal && modal.addEventListener("click", (e)=>{ if(e.target === modal) closeModal(); });



  function getVisibleIndustryCounts(){
    const counts = new Map();
    $$("#resultsTable tbody tr").forEach(tr=>{
      if(tr.style.display === "none") return;
      const key = tr.children[idx.industry].textContent.trim() || "(Unknown)";
      counts.set(key, (counts.get(key)||0)+1);
    });
    return Array.from(counts.entries()).sort((a,b)=>b[1]-a[1]);
  }
  function hue(i, total){ return Math.round((360 * i) / Math.max(1,total)); }
  function color(i,total){ return `hsl(${hue(i,total)},70%,55%)`; }
  function renderIndustryPie(){
    if(!canvas) return;
    const ctx = canvas.getContext("2d");
    const W = canvas.width, H = canvas.height;
    ctx.clearRect(0,0,W,H);
    const data = getVisibleIndustryCounts();
    const total = data.reduce((s, [,v])=>s+v, 0) || 1;
    const cx = W*0.4, cy = H*0.5;
    const r  = Math.min(W, H)*0.38;
    let start = -Math.PI/2;
    data.forEach(([name, value], i)=>{
      const slice = (value/total) * Math.PI*2;
      const end = start + slice;
      ctx.beginPath(); ctx.moveTo(cx, cy);
      ctx.arc(cx, cy, r, start, end); ctx.closePath(); ctx.fillStyle = color(i, data.length);
      ctx.fill(); start = end;
    });
    ctx.fillStyle = "#333"; ctx.font = "14px system-ui, -apple-system, Segoe UI, Roboto, Arial";
    ctx.fillText(`Total: ${total}`, 16, 22);
    if(legend){
      legend.innerHTML = "";
      data.forEach(([name, value], i)=>{
        const percent = ((value/total)*100).toFixed(1);
        const row = document.createElement("div");
        row.className = "legend-item";
        row.innerHTML = `
          <span class="swatch" style="background:${color(i,data.length)}"></span>
          <span>${name}</span>
          <span style="margin-left:auto; opacity:.8">${value} (${percent}%)</span>
        `;
        legend.appendChild(row);
      });
    }
  }

  // Row modal
  const rowModal = $("#row_modal_backdrop");
  const rowModalClose = $("#row_modal_close");
  const rowModalBody  = $("#row_modal_body");
  const rowModalTitle = $("#row_modal_title");
  const btnCopyJson   = $("#btn_copy_json");
  function openRowModal(){ if(!rowModal) return; rowModal.style.display = "flex"; document.body.classList.add("modal-open"); }
  function closeRowModal(){ if(!rowModal) return; rowModal.style.display = "none"; document.body.classList.remove("modal-open"); }
  rowModalClose && rowModalClose.addEventListener("click", closeRowModal);
  rowModal && rowModal.addEventListener("click", (e)=>{ if(e.target === rowModal) closeRowModal(); });
  document.addEventListener("keydown", (e)=>{ if(e.key === "Escape") closeRowModal(); });
  const headers = $$("#resultsTable thead th").map(th => th.textContent.trim());
  tbody.addEventListener("click", (e)=>{
    const tr = e.target.closest("tr");
    if(!tr || !tbody.contains(tr)) return;
    const rec = {}; headers.forEach((h, i)=>{ rec[h] = tr.children[i]?.textContent.trim() ?? ""; });
    const title = rec["Name"] || rec["NSE Code"] || "Record Details";
    if(rowModalTitle) rowModalTitle.textContent = title;
    const html = [
      '<table class="kv-table">',
      ...headers.map(h=>{
        const v = rec[h];
        const show = v ? v : '<span style="opacity:.6">(empty)</span>';
        return `<tr><th>${h}</th><td>${show}</td></tr>`;
      }),
      '</table>'
    ].join("");
    if(rowModalBody) rowModalBody.innerHTML = html;
    if(btnCopyJson){
      btnCopyJson.onclick = async ()=>{
        try{ await navigator.clipboard.writeText(JSON.stringify(rec, null, 2));
          btnCopyJson.textContent = "Copied!"; setTimeout(()=>btnCopyJson.textContent="Copy JSON",1200);
        }catch(err){ alert("Could not copy JSON"); }
      };
    }
    openRowModal();
  });

})();

// Off-canvas toggle (persist per route)
(function(){
  const pageWrap   = document.querySelector('.page-wrap');
  const toggleBtn  = document.getElementById('btn_toggle_filters');
  const handleBtn  = document.getElementById('btn_filters_handle');
  if(!pageWrap || !toggleBtn) return;

  const storageKey = location.pathname + ':filtersOffcanvas';
  function apply(hidden){
    pageWrap.classList.toggle('filters-offcanvas', hidden);
    toggleBtn.textContent = hidden ? '🙉 Show' : '🪄 Hide';
    toggleBtn.setAttribute('aria-pressed', String(hidden));
    toggleBtn.setAttribute('aria-expanded', String(!hidden));
    if (handleBtn) handleBtn.setAttribute('aria-hidden', String(!hidden));
  }
  const savedHidden = localStorage.getItem(storageKey) === '1';
  apply(savedHidden);

  toggleBtn.addEventListener('click', ()=>{
    const nowHidden = !pageWrap.classList.contains('filters-offcanvas');
    apply(nowHidden); localStorage.setItem(storageKey, nowHidden ? '1' : '0');
  });
  handleBtn && handleBtn.addEventListener('click', ()=>{
    apply(false); localStorage.setItem(storageKey, '0');
  });
})();
