(function(){
  const table = document.getElementById('holdingsTable');
  if (!table) return;

  const tbody = table.querySelector('tbody');
  const headers = table.querySelectorAll('th.sortable');

  const filterCompany  = document.getElementById('filterCompany');
  const filterBasket   = document.getElementById('filterBasket');
  const filterBasketId = document.getElementById('filterBasketId');
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
      investedRemainingAll = 0,   // <-- show this on the "Total Invested" card
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
  if (elInvested)  elInvested.textContent = '₹' + investedRemainingAll.toFixed(2);  // <-- changed
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

    Array.from(tbody.querySelectorAll('tr')).forEach(tr=>{
      const name   = (tr.dataset.company || '').toLowerCase();
      const bask   = tr.dataset.basket || '';
      const baskId = tr.dataset.basket_id || '';

      const matchName        = !nameQ || name.includes(nameQ);
      const matchBasketDrop  = !basketSel || bask === basketSel;
      const matchBasketId    = !basketIdQ || baskId.includes(basketIdQ);

      tr.style.display = (matchName && matchBasketDrop && matchBasketId) ? '' : 'none';
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

  filterCompany.addEventListener('input', applyFilters);
  filterBasket.addEventListener('change', applyFilters);
  filterBasketId.addEventListener('input', applyFilters);

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
        const investedRemaining = remainingQty * buyPrice;
        const currentValue = remainingQty * live;
        const unrealised = currentValue - investedRemaining;

        // Store for sorting/summary
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
      refreshSummaryFromVisible();
    });
}

  function hydrateLivePrices() {
    const rows = Array.from(tbody.querySelectorAll('tr'));
    rows.forEach((tr, idx) => {
      const id = tr.dataset.holding_id;
      const elLP = document.getElementById(`lp-${id}`);
      const elCV = document.getElementById(`cv-${id}`);
      const elUG = document.getElementById(`ug-${id}`);
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
  applyFilters();
})();
