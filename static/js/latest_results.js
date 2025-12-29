(function(){
  const $  = (s,p=document)=>p.querySelector(s);
  const $$ = (s,p=document)=>Array.from(p.querySelectorAll(s));

  const table = $("#resultsTable");
  if (!table) return;
  const tbody = table.tBodies[0];

  // Column indices updated for new structure
  const idx = {
    name:0, bse:1, nse:2, industry:3, price:4, mcap_cap:5, mcap:6,
    eps_lq:7, eps_pq:8, eps_pyq:9, roe:10, roce:11,
    pe:12, indpe:13, pegr:14, debt:15, dbttoeq:16,
    promoter:17, fii:18, dii:19, pub:20,
    r1w:21, r1m:22, r3m:23, r6m:24,
    date:25, scr:26, ess:27, tech:28, margin:29, tscore:30,
    deliv:31, series:32, high52:33, low52:34 // New indices
  };

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
      applyHighlights();
    });
  });

  function getCell(tr, i){ return tr.children[i].textContent.trim(); }
  function toNum(v){
    if(!v) return NaN;
    const s = v.replace(/[^\d.+\-eE]/g,'');
    if(!s || s==='+'||s==='-'||s==='.') return NaN;
    return parseFloat(s);
  }
  function compare(a,b,type){
    if(type==="num"){
      const x=toNum(a), y=toNum(b);
      if(isNaN(x)&&isNaN(y)) return 0;
      if(isNaN(x)) return 1;
      if(isNaN(y)) return -1;
      return x-y;
    } else if(type==="date"){
      return new Date(a) - new Date(b);
    } else {
      return a.localeCompare(b, undefined, {sensitivity:"base"});
    }
  }

  // ----- High/Low Distance Logic -----
  function updateDistances() {
    $$('.dist-container').forEach(container => {
      const price = parseFloat(container.dataset.price);
      const high = parseFloat(container.dataset.high);
      const low = parseFloat(container.dataset.low);

      if (!isNaN(price) && !isNaN(high) && high !== 0) {
        const offHigh = ((price - high) / high * 100).toFixed(1);
        container.querySelector('.dist-high').textContent = `${offHigh}% from High`;
      }
      if (!isNaN(price) && !isNaN(low) && low !== 0) {
        const upFromLow = ((price - low) / low * 100).toFixed(1);
        container.querySelector('.dist-low').textContent = `+${upFromLow}% from Low`;
      }
    });
  }

  // ----- Filters -----
  const F = {
    name: $("#f_name"), industryMulti: $("#f_industry_multi"),
    pe_min: $("#f_pe_min"), pe_max: $("#f_pe_max"),
    roe_min_r: $("#f_roe_min_r"), roe_hint: $("#f_roe_hint"),
    roce_min_r: $("#f_roce_min_r"), roce_hint: $("#f_roce_hint"),
    mcap_multi: $("#f_mcap_multi"), ess_min_r: $("#f_ess_min_r"), ess_hint: $("#f_ess_hint"),
    mc_tech_multi: $("#f_mc_tech_multi"), btn_reset: $("#btn_reset"),
  };

  function applyHighlights(){
    $$("#resultsTable tbody tr").forEach(tr=>{
      const c = tr.children;
      for (const td of c) td.classList.remove("bg-good","bg-bad");

      // EPS logic
      const lq = toNum(c[idx.eps_lq].textContent), pq = toNum(c[idx.eps_pq].textContent), pyq = toNum(c[idx.eps_pyq].textContent);
      if ([lq,pq,pyq].every(Number.isFinite)) {
        const ok = (lq > pq) && (lq > pyq);
        [c[idx.eps_lq], c[idx.eps_pq], c[idx.eps_pyq]].forEach(td => td.classList.add(ok ? "bg-good" : "bg-bad"));
      }
      // PE vs Industry PE
      const pe = toNum(c[idx.pe].textContent), indpe = toNum(c[idx.indpe].textContent);
      if ([pe,indpe].every(Number.isFinite)) { [c[idx.pe], c[idx.indpe]].forEach(td => td.classList.add(pe < indpe ? "bg-good" : "bg-bad")); }
      // ROE/ROCE
      const roe = toNum(c[idx.roe].textContent), roce = toNum(c[idx.roce].textContent);
      if ([roe,roce].every(Number.isFinite)) { [c[idx.roe], c[idx.roce]].forEach(td => td.classList.add((roe > 15 && roce > 15) ? "bg-good" : "bg-bad")); }
      // Scores
      const tscore = toNum(c[idx.tscore].textContent);
      if (Number.isFinite(tscore)) c[idx.tscore].classList.add(tscore >= 70 ? "bg-good" : "bg-bad");
      // Delivery % Highlight (New)
      const dper = toNum(c[idx.deliv].textContent);
      if (Number.isFinite(dper) && dper > 60) c[idx.deliv].classList.add("bg-good");
    });
  }

  // --- Filter Initialization ---
  function fillMultiSelect(selectEl, values){
    if(!selectEl) return; selectEl.innerHTML = "";
    values.sort().forEach(v=>{ const opt = document.createElement("option"); opt.value = opt.textContent = v; selectEl.appendChild(opt); });
  }
  function uniqueColumnValues(colIdx){
    const set = new Set();
    $$("#resultsTable tbody tr").forEach(tr=> { const val = tr.children[colIdx].textContent.trim(); if(val) set.add(val); });
    return Array.from(set);
  }
  fillMultiSelect(F.industryMulti, uniqueColumnValues(idx.industry));
  fillMultiSelect(F.mcap_multi, uniqueColumnValues(idx.mcap));
  fillMultiSelect(F.mc_tech_multi, uniqueColumnValues(idx.tech));

  function debounce(fn, ms){ let t; return (...args)=>{ clearTimeout(t); t=setTimeout(()=>fn.apply(this,args), ms); }; }
  function selectedValues(selectEl){ return Array.from((selectEl?.selectedOptions)||[]).map(o=>o.value.toLowerCase()); }
  
  function applyFilters(){
    const indS = new Set(selectedValues(F.industryMulti)), mcapS = new Set(selectedValues(F.mcap_multi)), techS = new Set(selectedValues(F.mc_tech_multi));
    $$("#resultsTable tbody tr").forEach(tr=>{
      const c = tr.children;
      const nameOk = !F.name.value || c[idx.name].textContent.toLowerCase().includes(F.name.value.toLowerCase());
      const indOk = indS.size === 0 || indS.has(c[idx.industry].textContent.toLowerCase());
      const mcapOk = mcapS.size === 0 || mcapS.has(c[idx.mcap].textContent.toLowerCase());
      const techOk = techS.size === 0 || techS.has(c[idx.tech].textContent.toLowerCase());
      tr.style.display = (nameOk && indOk && mcapOk && techOk) ? "" : "none";
    });
    applyHighlights();
  }

  // --- Events ---
  [F.name, F.industryMulti, F.mcap_multi, F.mc_tech_multi, F.pe_min, F.pe_max].forEach(el=>{
    if(!el) return; const evt = (el.tagName === "SELECT") ? "change" : "input";
    el.addEventListener(evt, debounce(applyFilters, 120));
  });

  // Toggle Filters Off-canvas
  $("#btn_toggle_filters").addEventListener('click', () => { $(".page-wrap").classList.toggle('filters-offcanvas'); });
  $("#btn_filters_handle").addEventListener('click', () => { $(".page-wrap").classList.remove('filters-offcanvas'); });

  // Init
  updateDistances();
  applyFilters();

  // Detail Modal
  tbody.addEventListener("click", (e)=>{
    const tr = e.target.closest("tr"); if(!tr) return;
    const headers = $$("#resultsTable thead th").map(th => th.textContent.trim());
    let html = '<table class="kv-table">';
    headers.forEach((h, i)=> { html += `<tr><th>${h}</th><td>${tr.children[i].textContent}</td></tr>`; });
    html += '</table>';
    $("#row_modal_title").textContent = tr.children[idx.name].textContent;
    $("#row_modal_body").innerHTML = html;
    $("#row_modal_backdrop").style.display = "flex";
  });
  $("#row_modal_close").addEventListener("click", () => { $("#row_modal_backdrop").style.display = "none"; });

})();