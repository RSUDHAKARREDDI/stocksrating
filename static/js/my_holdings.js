(function(){
  const table = document.getElementById('holdingsTable');
  if (!table) return;

  const tbody = table.querySelector('tbody');
  const headers = table.querySelectorAll('th.sortable');

  const filterCompany  = document.getElementById('filterCompany');
  const filterBasket   = document.getElementById('filterBasket');
  const filterBasketId = document.getElementById('filterBasketId');

  const btnLoadPrices  = document.getElementById('btn_load_prices');

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
      opt.value = v;
      opt.textContent = v;
      filterBasket.appendChild(opt);
    });
  })();

  function getRowValue(tr, key, type){
    const val = tr.dataset[key] ?? '';
    if (type === 'num') {
      const n = parseFloat(val);
      return isNaN(n) ? null : n;
    }
    return (val || '').toString().toLowerCase();
  }

  function refreshSummaryFromVisible(){
    const rows = Array.from(tbody.querySelectorAll('tr')).filter(tr => tr.style.display !== 'none');

    let totalRows = 0, investedAll = 0, sellOnly = 0, investedSoldOnly = 0;
    const companySet = new Set();

    rows.forEach(tr=>{
      totalRows++;
      const name = (tr.dataset.company || '').trim();
      if (name) companySet.add(name);

      const buyPrice  = parseFloat(tr.dataset.buy_price || '0') || 0;
      const buyQty    = parseFloat(tr.dataset.buy_qty   || '0') || 0;
      const sellQty   = parseFloat(tr.dataset.sell_qty  || '0') || 0;
      const sellValue = parseFloat(tr.dataset.sell_value|| '0') || 0;

      investedAll += buyQty * buyPrice;           // total invested (all buys)
      if (sellQty > 0){
        sellOnly += sellValue;                    // only sold value
        investedSoldOnly += sellQty * buyPrice;   // cost only for sold qty
      }
    });

    const net = sellOnly - investedSoldOnly;

    const cards = document.querySelectorAll('.summary-card .value');
    if (cards.length >= 5){
      cards[0].textContent = totalRows;
      cards[1].textContent = companySet.size;
      cards[2].textContent = '₹' + investedAll.toFixed(2);
      cards[3].textContent = '₹' + sellOnly.toFixed(2);
      cards[4].textContent = '₹' + net.toFixed(2);

      const plEl = cards[4];
      plEl.classList.remove('pos','neg','muted');
      plEl.classList.add(net > 0 ? 'pos' : (net < 0 ? 'neg' : 'muted'));
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

    headers.forEach(h=> h.querySelector('.arrow').textContent = '');
    const active = Array.from(headers).find(h => h.dataset.key === key);
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
  function fetchLivePrice(holdingId, el) {
    fetch(`/my_holdings/${holdingId}/price`)
      .then(r => r.json())
      .then(data => {
        if (data && !data.error && typeof data.price !== 'undefined') {
          el.textContent = `₹ ${Number(data.price).toFixed(2)}`;
          el.title = data.ticker ? `${data.ticker}${data.exchange ? ' | ' + data.exchange : ''}` : '';
        } else {
          el.textContent = 'NA';
          el.title = data && data.error ? data.error : '';
        }
      })
      .catch(() => { el.textContent = 'NA'; });
  }

  function hydrateLivePrices() {
    const cells = Array.from(document.querySelectorAll('[id^="lp-"]'));
    cells.forEach((el, idx) => {
      const id = el.id.replace('lp-', '');
      setTimeout(() => fetchLivePrice(id, el), idx * 120); // gentle staggering
    });
  }

  // Button triggers fetching (no auto-run to respect API limits)
  if (btnLoadPrices) {
    btnLoadPrices.addEventListener('click', ()=>{
      btnLoadPrices.disabled = true;
      const original = btnLoadPrices.textContent;
      btnLoadPrices.textContent = '⏳';
      hydrateLivePrices();
      // Re-enable after a safe window (you can refine with promise tracking if needed)
      setTimeout(()=>{
        btnLoadPrices.textContent = original;
        btnLoadPrices.disabled = false;
      }, 1500);
    });
  }

  // Initial summary/filters only (no live-price calls)
  applyFilters();
})();
