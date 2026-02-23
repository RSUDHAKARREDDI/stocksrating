// my_holdings.js (server-preferred avg_buy_price, safe version)
// Replace your existing my_holdings.js with this file.

(function(){
  const table = document.getElementById('holdingsTable');
  if (!table) return;

  const tbody = table.querySelector('tbody');
  const headers = table.querySelectorAll('th.sortable');

  const filterCompany  = document.getElementById('filterCompany');
  const filterBasket   = document.getElementById('filterBasket');
  const filterBasketId = document.getElementById('filterBasketId');
  const filterPosition = document.getElementById('filterPosition');
  const btnLoadPrices  = document.getElementById('btn_load_prices');

  const elTotal       = document.getElementById('card_total');
  const elCompanies   = document.getElementById('card_companies');
  const elInvested    = document.getElementById('card_invested');
  const elCurrent     = document.getElementById('card_current');
  const elUnrealised  = document.getElementById('card_unrealised');
  const elSell        = document.getElementById('card_sell');
  const elRealised    = document.getElementById('card_realised');

  let sortState = { key: null, dir: 'asc' };

  // small helper to parse numbers
  function toNum(x, d=0){ const n = parseFloat(x); return isNaN(n) ? d : n; }

  // Build basket filter options
  (function populateBasketFilter(){
    if (!filterBasket) return;
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

      if (sellQty > 0){
        sellOnly += sellValue;
        investedSoldOnly += sellQty * buyPrice;
      }

      let invRem = tr.dataset.invested_remaining;
      if (invRem === undefined || invRem === '' || invRem === null) {
        const remainingQty = Math.max(buyQty - sellQty, 0);
        invRem = remainingQty * buyPrice;
      } else {
        invRem = toNum(invRem, 0);
      }
      investedRemainingAll += invRem;

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
    const nameQ      = filterCompany ? filterCompany.value.trim().toLowerCase() : '';
    const basketSel  = filterBasket ? filterBasket.value : '';
    const basketIdQ  = filterBasketId ? filterBasketId.value.trim() : '';
    const posSel     = filterPosition ? filterPosition.value : 'both';

    Array.from(tbody.querySelectorAll('tr')).forEach(tr=>{
      const name   = (tr.dataset.company || '').toLowerCase();
      const bask   = tr.dataset.basket || '';
      const baskId = tr.dataset.basket_id || '';

      const matchName        = !nameQ || name.includes(nameQ);
      const matchBasketDrop  = !basketSel || bask === basketSel;
      const matchBasketId    = !basketIdQ || baskId.includes(basketIdQ);

      const sellQty = toNum(tr.dataset.sell_qty, 0);
      const positionState = (sellQty > 0) ? 'closed' : 'open';
      const matchPosition = (posSel === 'both' || !posSel) ? true : (posSel === positionState);

      tr.style.display = (matchName && matchBasketDrop && matchBasketId && matchPosition) ? '' : 'none';

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

  function getRowValue(tr, key, type){
    // ensure numeric parsing returns null when not present
    const val = tr.dataset[key] ?? '';
    if (type === 'num') {
      const n = parseFloat(val);
      return isNaN(n) ? null : n;
    }
    return (val || '').toString().toLowerCase();
  }

  headers.forEach(h=>{
    h.addEventListener('click', ()=> sortBy(h.dataset.key, h.dataset.type || 'text'));
  });

  if (filterCompany) filterCompany.addEventListener('input', applyFilters);
  if (filterBasket) filterBasket.addEventListener('change', applyFilters);
  if (filterBasketId) filterBasketId.addEventListener('input', applyFilters);
  if (filterPosition) filterPosition.addEventListener('change', applyFilters);

  // -----------------------
  // Company-level average computation (server-preferred)
  // - This function will NEVER overwrite a server-provided average.
  // - It accepts both attribute names: data-avg_buy_price and data-buy_avg_price.
  // -----------------------
  function computeCompanyAverages() {
    const totals = {}; // company -> { qty: n, invested: n, serverAvg: n|null }
    Array.from(tbody.querySelectorAll('tr')).forEach(tr => {
      const company = (tr.dataset.company || '').trim();
      if (!company) return;

      // check server-provided avg under both possible names
      const serverAvg1 = (tr.dataset.avg_buy_price !== undefined && tr.dataset.avg_buy_price !== '') ? toNum(tr.dataset.avg_buy_price, null) : null;
      const serverAvg2 = (tr.dataset.buy_avg_price !== undefined && tr.dataset.buy_avg_price !== '') ? toNum(tr.dataset.buy_avg_price, null) : null;
      const serverAvg = serverAvg1 !== null ? serverAvg1 : serverAvg2;

      if (!totals[company]) totals[company] = { qty: 0, invested: 0, serverAvg: null };

      if (serverAvg !== null && totals[company].serverAvg === null) {
        // Use first server-provided average found for the company (do not overwrite)
        totals[company].serverAvg = serverAvg;
      }

      // accumulate row-level totals as fallback if no serverAvg
      const rowQtyAttr = tr.dataset.buy_total_qty;
      const rowInvAttr = tr.dataset.buy_total_invested;

      if (rowQtyAttr !== undefined && rowQtyAttr !== '') {
        const rowQty = toNum(rowQtyAttr, 0);
        const rowInv = toNum(rowInvAttr, 0);
        totals[company].qty += rowQty;
        totals[company].invested += rowInv;
      } else {
        // fallback: use buy_qty * buy_price (per-row)
        const bq = toNum(tr.dataset.buy_qty, 0);
        const bp = toNum(tr.dataset.buy_price, 0);
        totals[company].qty += bq;
        totals[company].invested += (bq * bp);
      }
    });

    // Now compute effective avg for each company without overwriting server avg
    Object.keys(totals).forEach(company => {
      const t = totals[company];
      let avg;
      if (t.serverAvg !== null) {
        avg = t.serverAvg;
      } else {
        avg = t.qty > 0 ? (t.invested / t.qty) : 0;
      }

      // write dataset attribute BUT only if not present server-side
      // prefer to set both keys for compatibility, but do NOT clobber existing server-provided attr
      Array.from(tbody.querySelectorAll(`tr[data-company="${company.replace(/"/g,'&quot;')}"]`)).forEach(tr => {
        // If server provided avg in either attr name, do not overwrite it.
        const hasAvgAttr = (tr.dataset.avg_buy_price !== undefined && tr.dataset.avg_buy_price !== '') ||
                           (tr.dataset.buy_avg_price !== undefined && tr.dataset.buy_avg_price !== '');

        if (!hasAvgAttr) {
          // set both dataset names so sorting and other code will find it
          tr.dataset.avg_buy_price = avg.toFixed(6);
          tr.dataset.buy_avg_price = avg.toFixed(6);
        } else {
          // ensure UI shows server-provided value
          const provided = (tr.dataset.avg_buy_price !== undefined && tr.dataset.avg_buy_price !== '') ? tr.dataset.avg_buy_price : tr.dataset.buy_avg_price;
          tr.dataset.avg_buy_price = provided; // keep as-is
          tr.dataset.buy_avg_price = provided;
        }

        const holdingId = tr.dataset.holding_id;
        if (holdingId) {
          const elAvg = document.getElementById(`avg-${holdingId}`);
          if (elAvg) {
            // choose value from dataset (server preferred)
            const displayVal = tr.dataset.avg_buy_price || tr.dataset.buy_avg_price || '0';
            elAvg.textContent = Number(displayVal).toFixed(2);
          }
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

          // --- 52 Week Distance Calculation ---
          const elDist = document.getElementById(`dist-${holdingId}`);
          if (elDist) {
            const high = parseFloat(elDist.dataset.high);
            const low = parseFloat(elDist.dataset.low);
            const elHigh = elDist.querySelector('.dist-high');
            const elLow = elDist.querySelector('.dist-low');

            if (!isNaN(high) && high > 0) {
              const diffHigh = ((live - high) / high * 100).toFixed(1);
              elHigh.textContent = `${diffHigh}% from High`;
            }
            if (!isNaN(low) && low > 0) {
              const diffLow = ((live - low) / low * 100).toFixed(1);
              elLow.textContent = `+${((live - low) / low * 100).toFixed(1)}% from Low`;
            }
          }

          const buyQty   = toNum(tr.dataset.buy_qty);
          const sellQty  = toNum(tr.dataset.sell_qty);
          const buyPrice = toNum(tr.dataset.buy_price);
          const remainingQty = Math.max(buyQty - sellQty, 0);

          let investedRemaining = tr.dataset.invested_remaining;
          if (investedRemaining === undefined || investedRemaining === '' || investedRemaining === null) {
            investedRemaining = remainingQty * buyPrice;
          } else {
            investedRemaining = toNum(investedRemaining, 0);
          }

          const currentValue = remainingQty * live;
          const unrealised = currentValue - investedRemaining;

          tr.dataset.current_value = currentValue.toFixed(6);
          tr.dataset.unrealised = unrealised.toFixed(6);
          tr.dataset.invested_remaining = investedRemaining.toFixed(6);

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
        computeCompanyAverages();
        refreshSummaryFromVisible();
      });
  }

  function hydrateLivePrices() {
    // initial compute (server-preferred)
    computeCompanyAverages();

    const rows = Array.from(tbody.querySelectorAll('tr'));
    rows.forEach((tr, idx) => {
      const id = tr.dataset.holding_id;
      const elLP = document.getElementById(`lp-${id}`);
      const elCV = document.getElementById(`cv-${id}`);
      const elUG = document.getElementById(`ug-${id}`);

      // ensure UI shows avg immediately (prefer server-provided)
      const elAvg = document.getElementById(`avg-${id}`);
      if (elAvg) {
        const serverVal = (tr.dataset.avg_buy_price && tr.dataset.avg_buy_price !== '') ? tr.dataset.avg_buy_price
                         : (tr.dataset.buy_avg_price && tr.dataset.buy_avg_price !== '') ? tr.dataset.buy_avg_price
                         : null;
        if (serverVal !== null) {
          elAvg.textContent = Number(serverVal).toFixed(2);
        } else if (tr.dataset.avg_buy_price) {
          elAvg.textContent = Number(tr.dataset.avg_buy_price).toFixed(2);
        } else {
          const bp = toNum(tr.dataset.buy_price, 0);
          elAvg.textContent = bp.toFixed(2);
          tr.dataset.avg_buy_price = bp.toFixed(6);
          tr.dataset.buy_avg_price = bp.toFixed(6);
        }
      }

      if (!elLP || !elCV || !elUG) return;
      setTimeout(() => fetchLivePrice(id, elLP, elCV, elUG, tr), idx * 120);
    });
  }

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

function hydrateLivePrices() {
    fetch('/my_holdings/live_feed')
      .then(r => r.json())
      .then(liveData => {
        if (liveData.error) throw new Error(liveData.error);

        const rows = Array.from(tbody.querySelectorAll('tr'));
        rows.forEach(tr => {
            const id = tr.dataset.holding_id;
            const instrumentKey = tr.dataset.company;
            const livePrice = liveData[instrumentKey];

            if (livePrice !== undefined) {
                const live = parseFloat(livePrice);

                // 1. Update Live Price Cell
                const elLP = document.getElementById(`lp-${id}`);
                if (elLP) {
                    elLP.innerHTML = `<span style="color: #28a745; font-weight: bold;">₹${live.toFixed(2)}</span>`;
                }

                // 2. NEW: Update 52 Week Distance Calculations
                const elDist = document.getElementById(`dist-${id}`);
                if (elDist) {
                    const high = parseFloat(elDist.dataset.high);
                    const low = parseFloat(elDist.dataset.low);
                    const elHigh = elDist.querySelector('.dist-high');
                    const elLow = elDist.querySelector('.dist-low');

                    if (!isNaN(high) && high > 0) {
                        const diffHigh = ((live - high) / high * 100).toFixed(1);
                        elHigh.textContent = `${diffHigh}% from High`;
                    }
                    if (!isNaN(low) && low > 0) {
                        const diffLow = ((live - low) / low * 100).toFixed(1);
                        elLow.textContent = `+${((live - low) / low * 100).toFixed(1)}% from Low`;
                    }
                }

                // 3. Update Table Values (P/L and Current Value)
                const buyQty = toNum(tr.dataset.buy_qty);
                const sellQty = toNum(tr.dataset.sell_qty);
                const buyPrice = toNum(tr.dataset.buy_price);
                const remainingQty = Math.max(buyQty - sellQty, 0);

                const investedRemaining = toNum(tr.dataset.invested_remaining, remainingQty * buyPrice);
                const currentValue = remainingQty * live;
                const unrealised = currentValue - investedRemaining;

                tr.dataset.current_value = currentValue.toFixed(6);
                tr.dataset.unrealised = unrealised.toFixed(6);

                const elCV = document.getElementById(`cv-${id}`);
                const elUG = document.getElementById(`ug-${id}`);
                if (elCV) elCV.textContent = currentValue.toFixed(2);
                if (elUG) {
                    elUG.textContent = unrealised.toFixed(2);
                    setPLClass(elUG, unrealised);
                }
            }
        });
        refreshSummaryFromVisible();
    })
    .catch(err => console.error('Live Feed Error:', err));
}

// Automatically refresh prices every 5 seconds
setInterval(hydrateLivePrices, 5000);

  // initial
  computeCompanyAverages();
  applyFilters();

  // -----------------------
  // DEBUG helpers (remove or comment out in production)
  // -----------------------
  // Use these in console to inspect values:
  window.__holdings_debug = {
    getAllRows() { return Array.from(tbody.querySelectorAll('tr')).map(tr => ({
      holding_id: tr.dataset.holding_id,
      company: tr.dataset.company,
      buy_qty: tr.dataset.buy_qty,
      buy_price: tr.dataset.buy_price,
      avg_buy_price_attr: tr.dataset.avg_buy_price,
      buy_avg_price_attr: tr.dataset.buy_avg_price,
      invested_remaining: tr.dataset.invested_remaining
    })); }
  };

})();
