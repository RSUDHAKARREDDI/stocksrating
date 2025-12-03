// my_holdings.js — reads server-provided data-avg_buy_price (preferred) and falls back to per-row totals
(function(){
  const table = document.getElementById('holdingsTable');
  if (!table) return;

  const tbody = table.querySelector('tbody');
  const headers = table.querySelectorAll('th.sortable');

  const filterCompany  = document.getElementById('filterCompany');
  const filterBasket   = document.getElementById('filterBasket');
  const filterBasketId = document.getElementById('filterBasketId');

  // NEW: position filter (open/closed/both)
  const filterPosition = document.getElementById('filterPosition');

  const btnLoadPrices  = document.getElementById('btn_load_prices');

  // Summary card elements (ids are stable)
  const elTotal       = document.getElementById('card_total');
  const elCompanies   = document.getElementById('card_companies');
  const elInvested    = document.getElementById('card_invested');
  const elCurrent     = document.getElementById('card_current');
  const elUnrealised  = document.getElementById('card_unrealised');
  const elSell        = document.getElementById('card_sell');
  const elRealised    = document.getElementById('card_realised');

  let sortState = { key: null, dir: 'asc' }; // asc | desc

  // Build Basket dropdown from unique Basket IDs in the table
  (function populateBasketFilter(){
    const set = new Set();
    Array.from(tbody.querySelectorAll('tr')).forEach(tr=>{
      const v = tr.dataset.basket || '-';
      set.add(v);
    });
    const values = Array.from(set).sort((a,b)=>{
      if (a === '-') return 1; if (b === '-') return -1;
      const an = Number(a), bn = Number(b);
      const aNum = !isNaN(an), bNum = !isNaN(bn);
      if (aNum && bNum) return an - bn;
      if (aNum) return -1;
      if (bNum) return 1;
      return String(a).localeCompare(String(b));
    });
    values.forEach(v=>{
      if (v === '-') return;
      const opt = document.createElement('option');
      opt.value = v; opt.textContent = v;
      filterBasket.appendChild(opt);
    });
  })();

  function toNum(x, d=0){ const n = parseFloat(x); return isNaN(n) ? d : n; }

  function getRowValue(tr, key, type){
    const val = tr.dataset[key] ?? '';
    if (type === 'num') {
      const n = parseFloat(val);
      return isNaN(n) ? null : n;
    }
    return (val || '').toString().toLowerCase();
  }

  function setPLClass(el, v){
    el.classList.remove('pos','neg','muted');
    el.classList.add(v > 0 ? 'pos' : (v < 0 ? 'neg' : 'muted'));
  }

  function refreshSummaryFromVisible(){
    const rows = Array.from(tbody.querySelectorAll('tr')).filter(tr => tr.style.display !== 'none');

    let totalRows = 0,
        investedRemainingAll = 0,
        sellOnly = 0,
        investedSoldOnly = 0,
        currentAll = 0;

    const companySet = new Set();

    rows.forEach(tr=>{
      totalRows++;
      const name = (tr.dataset.company || '').trim();
      if (name) companySet.add(name);

      const buyPrice  = toNum(tr.dataset.buy_price);
      const buyQty    = toNum(tr.dataset.buy_qty);
      const sellQty   = toNum(tr.dataset.sell_qty);
      const sellValue = toNum(tr.dataset.sell_value);

      // For realised P/L (sold-only)
      if (sellQty > 0){
        sellOnly += sellValue;
        investedSoldOnly += sellQty * buyPrice;
      }

      // --- Invested (remaining only) ---
      let invRem = tr.dataset.invested_remaining;
      if (invRem === undefined || invRem === '' || invRem === null) {
        // fallback compute if attribute missing
        const remainingQty = Math.max(buyQty - sellQty, 0);
        invRem = remainingQty * buyPrice;
      } else {
        invRem = toNum(invRem, 0);
      }
      investedRemainingAll += invRem;

      // Current value is remainingQty * live (set after fetch); may be 0/NA before fetch
      const cv = toNum(tr.dataset.current_value, null);
      if (cv !== null) currentAll += cv;
    });

    const realised = sellOnly - investedSoldOnly;
    const unrealised = currentAll - investedRemainingAll;

    if (elTotal)     elTotal.textContent = totalRows;
    if (elCompanies) elCompanies.textContent = companySet.size;
    if (elInvested)  elInvested.textContent = '₹' + investedRemainingAll.toFixed(2);
    if (elSell)      elSell.textContent = '₹' + sellOnly.toFixed(2);

    if (elRealised) {
      elRealised.textContent = '₹' + realised.toFixed(2);
      setPLClass(elRealised, realised);
    }

    if (elCurrent)   elCurrent.textContent = '₹' + currentAll.toFixed(2);
    if (elUnrealised){
      elUnrealised.textContent = '₹' + unrealised.toFixed(2);
      setPLClass(elUnrealised, unrealised);
    }
  }

  function applyFilters(){
    const nameQ      = filterCompany.value.trim().toLowerCase();
    const basketSel  = filterBasket.value;
    const basketIdQ  = filterBasketId.value.trim();

    // NEW: get position filter (open/closed/both)
    const posSel     = filterPosition ? filterPosition.value : 'both'; // fallback 'both' if not present

    Array.from(tbody.querySelectorAll('tr')).forEach(tr=>{
      const name   = (tr.dataset.company || '').toLowerCase();
      const bask   = tr.dataset.basket || '';
      const baskId = tr.dataset.basket_id || '';

      const matchName        = !nameQ || name.includes(nameQ);
      const matchBasketDrop  = !basketSel || bask === basketSel;
      const matchBasketId    = !basketIdQ || baskId.includes(basketIdQ);

      // Determine position state from sell_qty
      const sellQty = toNum(tr.dataset.sell_qty, 0);
      const positionState = (sellQty > 0) ? 'closed' : 'open';
      const matchPosition = (posSel === 'both' || !posSel) ? true : (posSel === positionState);

      tr.style.display = (matchName && matchBasketDrop && matchBasketId && matchPosition) ? '' : 'none';

      // Update position badge text & classes
      const badge = tr.querySelector('.position-chip');
      if (badge) {
        badge.textContent = (positionState === 'open') ? 'Open' : 'Closed';
        badge.classList.toggle('open', positionState === 'open');
        badge.classList.toggle('closed', positionState === 'closed');
      }
    });

    refreshSummaryFromVisible();
  }

  function sortBy(key, type){
    const rows = Array.from(tbody.querySelectorAll('tr')).filter(tr => tr.style.display !== 'none');
    sortState.dir = (sortState.key === key && sortState.dir === 'asc') ? 'desc' : 'asc';
    sortState.key = key;

    rows.sort((a,b)=>{
      const av = getRowValue(a, key, type);
      const bv = getRowValue(b, key, type);

      if (av === null && bv === null) return 0;
      if (av === null) return 1;
      if (bv === null) return -1;

      if (type === 'num') return av - bv;
      if (av < bv) return -1;
      if (av > bv) return 1;
      return 0;
    });

    if (sortState.dir === 'desc') rows.reverse();

    const hidden = Array.from(tbody.querySelectorAll('tr')).filter(tr => tr.style.display === 'none');
    const frag = document.createDocumentFragment();
    rows.forEach(r => frag.appendChild(r));
    hidden.forEach(r => frag.appendChild(r));
    tbody.appendChild(frag);

    table.querySelectorAll('th.sortable .arrow').forEach(a=> a.textContent = '');
    const active = Array.from(table.querySelectorAll('th.sortable')).find(h => h.dataset.key === key);
    if (active) active.querySelector('.arrow').textContent = sortState.dir === 'asc' ? '▲' : '▼';

    refreshSummaryFromVisible();
  }

  headers.forEach(h=>{
    h.addEventListener('click', ()=> sortBy(h.dataset.key, h.dataset.type || 'text'));
  });

  // Wire up filter inputs
  filterCompany.addEventListener('input', applyFilters);
  filterBasket.addEventListener('change', applyFilters);
  filterBasketId.addEventListener('input', applyFilters);

  // NEW: wire position filter if present
  if (filterPosition) {
    filterPosition.addEventListener('change', applyFilters);
  }

  // -----------------------
  // Company-level average computation (prefers server-provided data-avg_buy_price)
  // -----------------------
  function computeCompanyAverages() {
    const totals = {}; // company -> { qty: n, invested: n, providedAvg: n|null }
    Array.from(tbody.querySelectorAll('tr')).forEach(tr => {
      const company = (tr.dataset.company || '').trim();
      if (!company) return;

      // check if server provided per-row company avg (data-avg_buy_price)
      const providedAvgAttr = tr.dataset.avg_buy_price;
      const providedAvg = (providedAvgAttr !== undefined && providedAvgAttr !== '') ? toNum(providedAvgAttr, null) : null;

      if (!totals[company]) totals[company] = { qty: 0, invested: 0, providedAvg: null };

      if (providedAvg !== null && totals[company].providedAvg === null) {
        // mark the provided avg for this company (first found)
        totals[company].providedAvg = providedAvg;
      }

      // still accumulate per-row values as a fallback if no provided avg exists
      // prefer explicit per-row totals if present (buy_total_qty/buy_total_invested)
      const rowQtyAttr = tr.dataset.buy_total_qty;
      const rowInvAttr = tr.dataset.buy_total_invested;

      if (rowQtyAttr !== undefined && rowQtyAttr !== '') {
        const rowQty = toNum(rowQtyAttr, 0);
        const rowInv = toNum(rowInvAttr, 0);
        totals[company].qty += rowQty;
        totals[company].invested += rowInv;
      } else {
        const bq = toNum(tr.dataset.buy_qty, 0);
        const bp = toNum(tr.dataset.buy_price, 0);
        totals[company].qty += bq;
        totals[company].invested += (bq * bp);
      }
    });

    // apply avg: if providedAvg exists for company use it, otherwise compute invested/qty
    Object.keys(totals).forEach(company => {
      const t = totals[company];
      let avg;
      if (t.providedAvg !== null) {
        avg = t.providedAvg;
      } else {
        avg = t.qty > 0 ? (t.invested / t.qty) : 0;
      }
      // set dataset avg_buy_price on every row of that company and update UI cell
      Array.from(tbody.querySelectorAll(`tr[data-company="${company.replace(/"/g,'&quot;')}"]`)).forEach(tr => {
        tr.dataset.avg_buy_price = avg.toFixed(6);
        const holdingId = tr.dataset.holding_id;
        if (holdingId) {
          const elAvg = document.getElementById(`avg-${holdingId}`);
          if (elAvg) elAvg.textContent = avg.toFixed(2);
        }
      });
    });
  }

  // ===== On-demand Live Prices =====
  function fetchLivePrice(holdingId, elPrice, elCV, elUG, tr) {
    fetch(`/my_holdings/${holdingId}/price`)
      .then(r => r.json())
      .then(data => {
        if (data && !data.error && typeof data.price !== 'undefined') {
          const live = Number(data.price);
          elPrice.textContent = `₹ ${live.toFixed(2)}`;
          elPrice.title = data.ticker ? `${data.ticker}${data.exchange ? ' | ' + data.exchange : ''}` : '';

          // === Correct unrealised logic: use remaining quantity only ===
          const buyQty   = toNum(tr.dataset.buy_qty);
          const sellQty  = toNum(tr.dataset.sell_qty);
          const buyPrice = toNum(tr.dataset.buy_price);

          const remainingQty = Math.max(buyQty - sellQty, 0);

          // invested_remaining may be present (server-side) or updated earlier; fallback compute
          let investedRemaining = tr.dataset.invested_remaining;
          if (investedRemaining === undefined || investedRemaining === '' || investedRemaining === null) {
            investedRemaining = remainingQty * buyPrice;
          } else {
            investedRemaining = toNum(investedRemaining, 0);
          }

          const currentValue = remainingQty * live;
          const unrealised = currentValue - investedRemaining;

          // Store for sorting/summary (these are per-row values)
          tr.dataset.current_value = currentValue.toFixed(6);
          tr.dataset.unrealised = unrealised.toFixed(6);
          tr.dataset.invested_remaining = investedRemaining.toFixed(6);

          // UI (show 0 when fully sold)
          elCV.textContent = currentValue.toFixed(2);
          elUG.textContent = unrealised.toFixed(2);
          setPLClass(elUG, unrealised);
        } else {
          elPrice.textContent = 'NA';
          elPrice.title = data && data.error ? data.error : '';
        }
      })
      .catch(() => { elPrice.textContent = 'NA'; })
      .finally(()=> {
        // After each price update, recompute company-level averages (in case any per-row totals changed)
        computeCompanyAverages();
        refreshSummaryFromVisible();
      });
  }

  function hydrateLivePrices() {
    // initial compute of company averages (prefers server-provided avg)
    computeCompanyAverages();

    const rows = Array.from(tbody.querySelectorAll('tr'));
    rows.forEach((tr, idx) => {
      const id = tr.dataset.holding_id;
      const elLP = document.getElementById(`lp-${id}`);
      const elCV = document.getElementById(`cv-${id}`);
      const elUG = document.getElementById(`ug-${id}`);
      // Ensure avg cell shows initial dataset value if present
      const elAvg = document.getElementById(`avg-${id}`);
      if (elAvg) {
        if (tr.dataset.avg_buy_price) {
          elAvg.textContent = Number(tr.dataset.avg_buy_price).toFixed(2);
        } else {
          const bp = toNum(tr.dataset.buy_price, 0);
          elAvg.textContent = bp.toFixed(2);
          tr.dataset.avg_buy_price = bp.toFixed(6);
        }
      }
      if (!elLP || !elCV || !elUG) return;
      setTimeout(() => fetchLivePrice(id, elLP, elCV, elUG, tr), idx * 120); // gentle staggering
    });
  }

  // Button triggers fetching (no auto-run to respect API limits)
  if (btnLoadPrices) {
    btnLoadPrices.addEventListener('click', ()=>{
      btnLoadPrices.disabled = true;
      const original = btnLoadPrices.textContent;
      btnLoadPrices.textContent = '⏳';
      hydrateLivePrices();
      setTimeout(()=>{
        btnLoadPrices.textContent = original;
        btnLoadPrices.disabled = false;
      }, 1500);
    });
  }

  // Initial summary/filters only (no live-price calls)
  computeCompanyAverages();
  applyFilters();
})();
