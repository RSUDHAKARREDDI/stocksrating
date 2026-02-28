(function(){
  const $  = (s,p=document)=>p.querySelector(s);
  const $$ = (s,p=document)=>Array.from(p.querySelectorAll(s));

  const table = $("#resultsTable");
  if (!table) return;
  const tbody = table.tBodies[0];

  /** * Recalibrated Indices for Quality Stocks */
  const idx = {
    name: 0,
    industryGroup: 3,
    industry: 4,
    price: 5,
    mcap_val: 6,
    mcap_text: 7,
    eps_lq: 8, eps_pq: 9, eps_pyq: 10,
    roe: 11, roce: 12, pe: 13, indpe: 14,
    debt: 16, dbttoeq: 17, pub: 21,
    r1w: 22, r1m: 23, scr: 27, ess: 28,
    tech: 29, tscore: 31, series: 33
  };

  // ----- UI Controls -----
  const pageWrap = $('.page-wrap');
  const toggleBtn = $('#btn_toggle_filters');
  const handleBtn = $('#btn_filters_handle');

  if (toggleBtn && handleBtn && pageWrap) {
    toggleBtn.addEventListener('click', () => pageWrap.classList.add('filters-offcanvas'));
    handleBtn.addEventListener('click', () => pageWrap.classList.remove('filters-offcanvas'));
  }

  function toNum(v){
    if(!v) return NaN;
    const s = v.toString().replace(/[^\d.+\-eE]/g,'');
    return (s===''||s==='+'||s==='-'||s==='.') ? NaN : parseFloat(s);
  }

  // ----- Dependent Filter Logic -----
  function updateIndustryOptions() {
    const groupSel = $("#f_industry_group_multi");
    const indSel = $("#f_industry_multi");
    if(!groupSel || !indSel) return;

    const selectedGroups = new Set(Array.from(groupSel.selectedOptions).map(o => o.value));
    const currentIndSelection = new Set(Array.from(indSel.selectedOptions).map(o => o.value));

    indSel.innerHTML = "";
    const availableIndustries = new Set();

    $$("#resultsTable tbody tr").forEach(tr => {
      const groupValue = tr.children[idx.industryGroup].textContent.trim();
      const indValue = tr.children[idx.industry].textContent.trim();
      if (selectedGroups.size === 0 || selectedGroups.has(groupValue)) {
        availableIndustries.add(indValue);
      }
    });

    Array.from(availableIndustries).sort().forEach(v => {
      const opt = new Option(v, v);
      if(currentIndSelection.has(v)) opt.selected = true;
      indSel.add(opt);
    });
  }

// ----- KPI Highlighting -----
  function applyHighlights() {
    const rows = Array.from(tbody.querySelectorAll("tr"));
    rows.forEach(tr => {
      if (tr.style.display === "none") return;
      const c = tr.children;

      // Clear existing highlights
      Array.from(c).forEach(td => td.classList.remove("bg-good", "bg-bad"));

      const check = (val, condition, cellIdx) => {
        if (!c[cellIdx]) return;
        const num = toNum(val);
        if (isNaN(num)) return; // Skip if not a number
        c[cellIdx].classList.add(condition(num) ? "bg-good" : "bg-bad");
      };

      // 1. EPS Growth logic (LQ > PQ AND LQ > PYQ)
      const lq = toNum(c[idx.eps_lq]?.textContent);
      const pq = toNum(c[idx.eps_pq]?.textContent);
      const pyq = toNum(c[idx.eps_pyq]?.textContent);
      const epsOk = lq > pq && lq > pyq;
      [idx.eps_lq, idx.eps_pq, idx.eps_pyq].forEach(i => {
        if (c[i]) c[i].classList.add(epsOk ? "bg-good" : "bg-bad");
      });

      // 2. Fundamental Highlighters
      check(c[idx.roe]?.textContent, n => n > 15, idx.roe);
      check(c[idx.roce]?.textContent, n => n > 15, idx.roce);
      check(c[idx.tscore]?.textContent, n => n >= 70, idx.tscore);
      check(c[idx.ess]?.textContent, n => n >= 70, idx.ess);

      // 3. PE, Industry PE, and PEG Ratio (Missing #1)
      const pe = toNum(c[idx.pe]?.textContent);
      const ipe = toNum(c[idx.indpe]?.textContent);
      const peOk = pe < ipe;
      [idx.pe, idx.indpe].forEach(i => {
        if (c[i]) c[i].classList.add(peOk ? "bg-good" : "bg-bad");
      });
      // PEG Ratio < 1 is generally considered good
      const pegIdx = 15; // Column 'PEG Ratio'
      check(c[pegIdx]?.textContent, n => n > 0 && n < 1, pegIdx);

      // 4. Debt to Equity (Missing #2)
      check(c[idx.dbttoeq]?.textContent, n => n < 1, idx.dbttoeq);

      // 5. Public Holding (Missing #3)
      // Low public holding is often preferred in "Quality" filters
      check(c[idx.pub]?.textContent, n => n < 25, idx.pub);

      // 6. Return Highlighters (Missing #4)
      // 1 Week: Green if > 0
      check(c[idx.r1w]?.textContent, n => n > 0, idx.r1w);
      // 1 Month: Green if > 10
      check(c[idx.r1m]?.textContent, n => n > 10, idx.r1m);

      // 7. 52W Distance calculation
      const distContainer = tr.querySelector('.dist-container');
      if (distContainer) {
        const p = parseFloat(distContainer.dataset.price);
        const h = parseFloat(distContainer.dataset.high);
        const l = parseFloat(distContainer.dataset.low);
        if (p && h && h !== 0) distContainer.querySelector('.dist-high').textContent = `${((p-h)/h*100).toFixed(1)}% off High`;
        if (p && l && l !== 0) distContainer.querySelector('.dist-low').textContent = `+${((p-l)/l*100).toFixed(1)}% from Low`;
      }
    });
  }

  // ----- Filter execution -----
  function applyFilters(){
    const f = {
      name: $("#f_name").value.toLowerCase(),
      indsGrp: new Set(Array.from($("#f_industry_group_multi").selectedOptions).map(o=>o.value.toLowerCase())),
      inds: new Set(Array.from($("#f_industry_multi").selectedOptions).map(o=>o.value.toLowerCase())),
      techs: new Set(Array.from($("#f_mc_tech_multi").selectedOptions).map(o=>o.value.toLowerCase())),
      mcaps: new Set(Array.from($("#f_mcap_multi").selectedOptions).map(o=>o.value.toLowerCase())),
      scrs: new Set(Array.from($("#f_scr_multi").selectedOptions).map(o=>o.value.toLowerCase())),
      peRel: $("#f_pe_rel").value,
      ranges: {
        tscore: [parseFloat($("#f_tscore_min").value), parseFloat($("#f_tscore_max").value)],
        ess: [parseFloat($("#f_ess_min").value), parseFloat($("#f_ess_max").value)],
        roe: [parseFloat($("#f_roe_min").value), parseFloat($("#f_roe_max").value)],
        roce: [parseFloat($("#f_roce_min").value), parseFloat($("#f_roce_max").value)],
        r1w: [parseFloat($("#f_r1w_min").value), parseFloat($("#f_r1w_max").value)],
        r1m: [parseFloat($("#f_r1m_min").value), parseFloat($("#f_r1m_max").value)]
      }
    };

    $$("#resultsTable tbody tr").forEach(tr=>{
      const c = tr.children;
      const pe = toNum(c[idx.pe].textContent), indPe = toNum(c[idx.indpe].textContent);

      const inRange = (val, r) => {
        const n = toNum(val);
        if(!isNaN(r[0]) && n < r[0]) return false;
        if(!isNaN(r[1]) && n > r[1]) return false;
        return true;
      };

      const ok =
        (!f.name || c[idx.name].textContent.toLowerCase().includes(f.name)) &&
        (f.indsGrp.size === 0 || f.indsGrp.has(c[idx.industryGroup].textContent.toLowerCase())) &&
        (f.inds.size === 0 || f.inds.has(c[idx.industry].textContent.toLowerCase())) &&
        (f.techs.size === 0 || f.techs.has(c[idx.tech].textContent.toLowerCase())) &&
        (f.mcaps.size === 0 || f.mcaps.has(c[idx.mcap_text].textContent.toLowerCase())) &&
        (f.scrs.size === 0 || f.scrs.has(c[idx.scr].textContent.toLowerCase())) &&
        inRange(c[idx.tscore].textContent, f.ranges.tscore) &&
        inRange(c[idx.ess].textContent, f.ranges.ess) &&
        inRange(c[idx.roe].textContent, f.ranges.roe) &&
        inRange(c[idx.roce].textContent, f.ranges.roce) &&
        inRange(c[idx.r1w].textContent, f.ranges.r1w) &&
        inRange(c[idx.r1m].textContent, f.ranges.r1m) &&
        (f.peRel === 'all' || (f.peRel === 'under' ? pe < indPe : pe > indPe));

      tr.style.display = ok ? "" : "none";
    });
    applyHighlights();
  }

  // --- CSV Download ---
  $("#btn_download_csv").onclick = () => {
    const rows = $$("#resultsTable tr");
    let csvContent = "";

    rows.forEach(tr => {
      // Export headers and only rows that are currently visible
      if (tr.parentElement.tagName === 'THEAD' || tr.style.display !== "none") {
        const cols = Array.from(tr.querySelectorAll("th, td"))
          .map(td => {
            // Clean text: remove extra whitespace and escape quotes
            let text = td.innerText.replace(/"/g, '""').trim();
            return `"${text}"`;
          })
          .join(",");
        csvContent += cols + "\r\n";
      }
    });

    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const link = document.createElement("a");
    const url = URL.createObjectURL(blob);
    link.setAttribute("href", url);
    link.setAttribute("download", `quality_stocks_export.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // --- Sorting & Init ---
  function fillMulti(id, col){
    const sel=$(id); if(!sel) return;
    const vals=new Set(); $$("#resultsTable tbody tr").forEach(tr=>vals.add(tr.children[col].textContent.trim()));
    Array.from(vals).filter(v=>v).sort().forEach(v=>sel.add(new Option(v,v)));
  }

  const debounce = (fn, ms) => { let t; return (...args)=>{ clearTimeout(t); t=setTimeout(()=>fn(...args),ms); }; };

  $$(".filters input, .filters select").forEach(el => {
    el.addEventListener("input", debounce(() => {
      if (el.id === "f_industry_group_multi") updateIndustryOptions();
      applyFilters();
    }, 150));
  });

  $("#btn_reset").onclick = () => location.reload();

  // Run Setup
  fillMulti("#f_industry_group_multi", idx.industryGroup);
  updateIndustryOptions();
  fillMulti("#f_mc_tech_multi", idx.tech);
  fillMulti("#f_mcap_multi", idx.mcap_text);
  fillMulti("#f_scr_multi", idx.scr);
  applyFilters();

  // ----- 7. Unified Record Details Popup -----
// ----- Unified Single-Line Record Details -----
  const rowModal = $("#row_modal_backdrop");
  const rowBody = $("#row_modal_body");
  const rowTitle = $("#row_modal_title");
  const rowClose = $("#row_modal_close");

  if (rowModal && tbody) {
    tbody.addEventListener("click", (e) => {
      const tr = e.target.closest("tr");
      // Don't trigger if clicking a button or link inside the row
      if (!tr || e.target.closest('button, a')) return;

      const headers = $$("#resultsTable thead th");
      const cells = tr.children;
      const rowData = {};

      rowTitle.textContent = cells[idx.name].innerText.split('\n')[0].trim();
      rowBody.innerHTML = "";

      headers.forEach((th, i) => {
        const label = th.textContent.trim();
        // Skip hidden columns or empty headers
        if (!label || window.getComputedStyle(th).display === 'none') return;

        const value = cells[i].innerText.split('\n')[0].trim();
        rowData[label] = value;

        const item = document.createElement("div");
        item.className = "detail-row";
        item.innerHTML = `
          <span class="detail-label">${label}</span>
          <span class="detail-filler"></span>
          <span class="detail-value">${value || '-'}</span>
        `;
        rowBody.appendChild(item);
      });

      $("#btn_copy_json").onclick = () => {
        navigator.clipboard.writeText(JSON.stringify(rowData, null, 2));
        alert("Details copied to clipboard!");
      };

      rowModal.style.display = "flex";
      document.body.style.overflow = "hidden";
    });

    const closeRowModal = () => {
      rowModal.style.display = "none";
      document.body.style.overflow = "auto";
    };

    rowClose.onclick = closeRowModal;
    window.addEventListener("click", (e) => { if (e.target === rowModal) closeRowModal(); });
  }

})();

