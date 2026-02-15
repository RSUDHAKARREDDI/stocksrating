(function(){
  const $  = (s,p=document)=>p.querySelector(s);
  const $$ = (s,p=document)=>Array.from(p.querySelectorAll(s));

  const table = $("#resultsTable");
  if (!table) return;
  const tbody = table.tBodies[0];

  const idx = {
    name:0, industry:3, price:4, eps_lq:7, eps_pq:8, eps_pyq:9,
    roe:10, roce:11, pe:12, indpe:13, pegr:14, dbttoeq:16, pub:20,
    r1w:21, r1m:22, r3m:23, r6m:24, scr:26, ess:27, tech:28, tscore:30
  };

  // ----- Filter Menu Hide/Show Logic -----
  const pageWrap = $('.page-wrap');
  const toggleBtn = $('#btn_toggle_filters');
  const handleBtn = $('#btn_filters_handle');

  if (toggleBtn && handleBtn && pageWrap) {
    toggleBtn.addEventListener('click', () => {
      pageWrap.classList.add('filters-offcanvas');
    });

    handleBtn.addEventListener('click', () => {
      pageWrap.classList.remove('filters-offcanvas');
    });
  }

  function toNum(v){
    if(!v) return NaN;
    const s = v.toString().replace(/[^\d.+\-eE]/g,'');
    return (s===''||s==='+'||s==='-'||s==='.') ? NaN : parseFloat(s);
  }

  // ----- Column Sorting Logic -----
  let sortState = { col: null, dir: 1 };
  $$("#resultsTable thead th").forEach((th, i) => {
    th.addEventListener("click", () => {
      const type = th.dataset.type || "text";
      sortState.dir = (sortState.col === i) ? -sortState.dir : 1;
      sortState.col = i;

      $$("#resultsTable thead th").forEach(h => h.classList.remove("sort-asc", "sort-desc"));
      th.classList.add(sortState.dir === 1 ? "sort-asc" : "sort-desc");

      const rows = $$("#resultsTable tbody tr");
      rows.sort((a, b) => {
        const valA = a.children[i].textContent.trim();
        const valB = b.children[i].textContent.trim();

        if (type === "num") {
          const nA = toNum(valA), nB = toNum(valB);
          return (isNaN(nA) && isNaN(nB)) ? 0 : isNaN(nA) ? 1 : isNaN(nB) ? -1 : (nA - nB) * sortState.dir;
        }
        return valA.localeCompare(valB) * sortState.dir;
      });

      rows.forEach(r => tbody.appendChild(r));
    });
  });

  // Highlights
  function applyHighlights() {
  const table = document.getElementById("resultsTable");
  const tbody = table.tBodies[0];
  const headerCells = Array.from(table.querySelectorAll('thead th')).map(th => th.textContent.trim().toLowerCase());

  // Helper to dynamically find indices based on header names
  const getIdx = (name) => headerCells.indexOf(name.toLowerCase());

  const idxMap = {
    eps_lq: getIdx("EPS latest quarter"),
    eps_pq: getIdx("EPS preceding quarter"),
    eps_pyq: getIdx("EPS preceding year quarter"),
    roe: getIdx("Return on equity"),
    roce: getIdx("Return on capital employed"),
    pe: getIdx("Price to Earning"),
    indpe: getIdx("Industry PE"),
    dte: getIdx("Debt to equity"),
    pub: getIdx("Public holding"),
    r1w: getIdx("Return over 1week"),
    r1m: getIdx("Return over 1month"),
    ess: getIdx("mc essentials"),
    tech: getIdx("mc technicals"),
    score: getIdx("Total Score"),
    series: getIdx("Series")
  };

  const rows = Array.from(tbody.querySelectorAll("tr"));

  rows.forEach(tr => {
    if (tr.style.display === "none") return;
    const c = tr.children;

    // Reset previous highlights
    Array.from(c).forEach(td => td.classList.remove("bg-good", "bg-bad"));

    const check = (val, condition, cellIdx) => {
      if (cellIdx === -1 || !c[cellIdx]) return;
      const num = parseFloat(val.toString().replace(/[^\d.+\-eE]/g, ''));
      const isGood = condition(num, val);
      c[cellIdx].classList.add(isGood ? "bg-good" : "bg-bad");
    };

    // 1. EPS Momentum: LQ > PQ AND LQ > PYQ (Highlight all 3 columns)
    const lq = toNum(c[idxMap.eps_lq]?.textContent);
    const pq = toNum(c[idxMap.eps_pq]?.textContent);
    const pyq = toNum(c[idxMap.eps_pyq]?.textContent);
    const epsOk = lq > pq && lq > pyq;
    [idxMap.eps_lq, idxMap.eps_pq, idxMap.eps_pyq].forEach(i => {
      if (i !== -1) c[i].classList.add(epsOk ? "bg-good" : "bg-bad");
    });

    // 2. ROE > 15
    check(c[idxMap.roe]?.textContent || "", (n) => n > 15, idxMap.roe);

    // 3. ROCE > 15
    check(c[idxMap.roce]?.textContent || "", (n) => n > 15, idxMap.roce);

    // 4. PE < Industry PE (Highlight both columns)
    const pe = toNum(c[idxMap.pe]?.textContent);
    const ipe = toNum(c[idxMap.indpe]?.textContent);
    const peOk = pe < ipe;
    [idxMap.pe, idxMap.indpe].forEach(i => {
      if (i !== -1) c[i].classList.add(peOk ? "bg-good" : "bg-bad");
    });

    // 5. Debt to Equity < 1
    check(c[idxMap.dte]?.textContent || "", (n) => n < 1, idxMap.dte);

    // 6. Public Holding < 25
    check(c[idxMap.pub]?.textContent || "", (n) => n < 25, idxMap.pub);

    // 7. Return over 1 Week > 0
    check(c[idxMap.r1w]?.textContent || "", (n) => n > 0, idxMap.r1w);

    // 8. Return over 1 Month > 10
    check(c[idxMap.r1m]?.textContent || "", (n) => n > 10, idxMap.r1m);

    // 9. MC Essential >= 70
    check(c[idxMap.ess]?.textContent || "", (n) => n >= 70, idxMap.ess);

    // 10. MC Technicals = Bullish/Very Bullish
    if (idxMap.tech !== -1 && c[idxMap.tech]) {
      const txt = c[idxMap.tech].textContent.toLowerCase();
      const isGood = txt.includes("bullish");
      c[idxMap.tech].classList.add(isGood ? "bg-good" : "bg-bad");
    }

    // 11. Total Score >= 70
    check(c[idxMap.score]?.textContent || "", (n) => n >= 70, idxMap.score);

    // 12. Series = EQ
    if (idxMap.series !== -1 && c[idxMap.series]) {
      const isEq = c[idxMap.series].textContent.trim().toUpperCase() === "EQ";
      c[idxMap.series].classList.add(isEq ? "bg-good" : "bg-bad");
    }

    // Restore 52-Week Distance Logic
    const distContainer = tr.querySelector('.dist-container');
    if (distContainer) {
      const p = parseFloat(distContainer.dataset.price);
      const h = parseFloat(distContainer.dataset.high);
      const l = parseFloat(distContainer.dataset.low);
      if (!isNaN(p) && !isNaN(h) && h !== 0) {
        distContainer.querySelector('.dist-high').textContent = `${((p - h) / h * 100).toFixed(1)}% off High`;
      }
      if (!isNaN(p) && !isNaN(l) && l !== 0) {
        distContainer.querySelector('.dist-low').textContent = `+${((p - l) / l * 100).toFixed(1)}% from Low`;
      }
    }
  });
}

  // Multi-select populate
  function fillMulti(id, col){
    const sel=$(id); if(!sel) return;
    const vals=new Set(); $$("#resultsTable tbody tr").forEach(tr=>vals.add(tr.children[col].textContent.trim()));
    Array.from(vals).filter(v=>v).sort().forEach(v=>sel.add(new Option(v,v)));
  }

  // Filter Logic
  function applyFilters(){
    const f = {
      name: $("#f_name").value.toLowerCase(),
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
      const pe=toNum(c[idx.pe].textContent), ind=toNum(c[idx.indpe].textContent);

      const inRange = (val, r) => {
        const n = toNum(val);
        if(isNaN(n)) return true;
        if(!isNaN(r[0]) && n < r[0]) return false;
        if(!isNaN(r[1]) && n > r[1]) return false;
        return true;
      };

      const ok =
        (!f.name || c[idx.name].textContent.toLowerCase().includes(f.name)) &&
        (f.inds.size === 0 || f.inds.has(c[idx.industry].textContent.toLowerCase())) &&
        (f.techs.size === 0 || f.techs.has(c[idx.tech].textContent.toLowerCase())) &&
        (f.mcaps.size === 0 || f.mcaps.has(c[6].textContent.toLowerCase())) &&
        (f.scrs.size === 0 || f.scrs.has(c[idx.scr].textContent.toLowerCase())) &&
        inRange(c[idx.tscore].textContent, f.ranges.tscore) &&
        inRange(c[idx.ess].textContent, f.ranges.ess) &&
        inRange(c[idx.roe].textContent, f.ranges.roe) &&
        inRange(c[idx.roce].textContent, f.ranges.roce) &&
        inRange(c[idx.r1w].textContent, f.ranges.r1w) &&
        inRange(c[idx.r1m].textContent, f.ranges.r1m) &&
        (f.peRel === 'all' || (f.peRel === 'under' ? pe < ind : pe > ind));

      tr.style.display = ok ? "" : "none";
    });
    applyHighlights();
  }

  const debounce = (fn, ms) => { let t; return (...args)=>{ clearTimeout(t); t=setTimeout(()=>fn(...args),ms); }; };
  $$(".filters input, .filters select").forEach(el=>el.addEventListener("input", debounce(applyFilters, 150)));
  $("#btn_reset").onclick = () => location.reload();

  // Distances
  function updateDistances() {
    $$('.dist-container').forEach(cnt => {
      const p=parseFloat(cnt.dataset.price), h=parseFloat(cnt.dataset.high), l=parseFloat(cnt.dataset.low);
      if(p && h) cnt.querySelector('.dist-high').textContent = `${((p-h)/h*100).toFixed(1)}% off High`;
      if(p && l) cnt.querySelector('.dist-low').textContent = `+${((p-l)/l*100).toFixed(1)}% from Low`;
    });
  }

  // Row Details Modal Logic
  const rowModal = $("#row_modal_backdrop");
  if (tbody && rowModal) {
    tbody.addEventListener("click", (e) => {
      const tr = e.target.closest("tr");
      if (!tr || !tbody.contains(tr)) return;
      const headers = $$("#resultsTable thead th").map(th => th.textContent.trim());
      let html = '<table class="kv-table">';
      headers.forEach((h, i) => {
        const val = tr.children[i]?.textContent.trim() || "";
        html += `<tr><th>${h}</th><td>${val || '<span style="opacity:0.5">(empty)</span>'}</td></tr>`;
      });
      html += '</table>';
      $("#row_modal_title").textContent = tr.children[idx.name].textContent;
      $("#row_modal_body").innerHTML = html;
      rowModal.style.display = "flex";
      document.body.classList.add("modal-open");
    });
  }

  $("#row_modal_close")?.addEventListener("click", () => {
    rowModal.style.display = "none";
    document.body.classList.remove("modal-open");
  });

  // INITIAL CALLS: Populate values and apply initial view
  fillMulti("#f_industry_multi", idx.industry);
  fillMulti("#f_mc_tech_multi", idx.tech);
  fillMulti("#f_mcap_multi", 6);
  fillMulti("#f_scr_multi", idx.scr);

  applyFilters();
  updateDistances();
})();

(function() {
  const downloadBtn = document.getElementById('btn_download_csv');

  if (downloadBtn) {
    downloadBtn.addEventListener('click', function() {
      const table = document.getElementById('resultsTable');
      if (!table) return;

      const rows = Array.from(table.querySelectorAll('tr'));
      if (rows.length === 0) return;

      // 1. Map Headers (Only columns that are not explicitly hidden for filtering)
      const headerRow = rows[0];
      const headerCells = Array.from(headerRow.querySelectorAll('th'));

      const visibleColIndices = [];
      const headers = [];

      headerCells.forEach((th, index) => {
        // Only include columns that are visible in the UI
        if (window.getComputedStyle(th).display !== 'none') {
          visibleColIndices.push(index);
          headers.push(`"${th.textContent.trim().replace(/"/g, '""')}"`);
        }
      });

      // 2. Map Filtered Data Rows
      const csvData = rows.slice(1)
        .filter(tr => tr.style.display !== 'none') // Only include visible rows
        .map(tr => {
          return visibleColIndices.map(index => {
            const td = tr.children[index];
            if (!td) return '""';

            let text = "";
            const priceVal = td.querySelector('.price-val');

            if (priceVal) {
              // Extract just the numerical price, ignoring the 52-week badges
              text = priceVal.textContent.trim();
            } else {
              // Clean badges and extra whitespace from other cells
              text = td.innerText.split('\n')[0].trim();
            }

            return `"${text.replace(/"/g, '""')}"`;
          }).join(',');
        });

      // 3. Create Blob with BOM for Excel UTF-8 Compatibility
      const BOM = "\uFEFF";
      const csvContent = BOM + headers.join(',') + '\n' + csvData.join('\n');
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);

      // 4. Trigger Download
      const link = document.createElement('a');
      link.href = url;
      link.download = `Stock_Data_${new Date().toISOString().slice(0,10)}.csv`;
      document.body.appendChild(link);
      link.click();

      // Cleanup
      setTimeout(() => {
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
      }, 100);
    });
  }
})();