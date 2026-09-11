(function () {
  var input = document.getElementById('site-search-input');
  var resultsBox = document.getElementById('site-search-results');
  if (!input || !resultsBox) return;

  var allItems = [];

  function normalize(str) {
    return str.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
  }

  fetch('/search.json')
    .then(function (res) { return res.json(); })
    .then(function (data) { allItems = data; })
    .catch(function (err) { console.error('Erro ao carregar search.json:', err); });

  function renderResults(items) {
    if (items.length === 0) {
      resultsBox.innerHTML = '<div class="search-empty">Nada encontrado.</div>';
      resultsBox.style.display = 'block';
      return;
    }
    var html = items.slice(0, 6).map(function (item) {
      return '<a href="' + item.url + '" class="search-result-item">' +
        '<span class="search-result-category">' + item.category + '</span>' +
        '<span class="search-result-title">' + item.title + '</span>' +
        '</a>';
    }).join('');
    resultsBox.innerHTML = html;
    resultsBox.style.display = 'block';
  }

  input.addEventListener('input', function () {
    var query = input.value.trim();
    if (query.length < 2) {
      resultsBox.style.display = 'none';
      return;
    }
    var q = normalize(query);
    var filtered = allItems.filter(function (item) {
      return normalize(item.title).indexOf(q) !== -1 ||
             normalize(item.excerpt || '').indexOf(q) !== -1;
    });
    filtered.sort(function (a, b) {
      return new Date(b.date) - new Date(a.date);
    });
    renderResults(filtered);
  });

  document.addEventListener('click', function (e) {
    if (!resultsBox.contains(e.target) && e.target !== input) {
      resultsBox.style.display = 'none';
    }
  });
})();
