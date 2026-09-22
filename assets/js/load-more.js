(function () {
  var PAGE_SIZE = 12;

  document.querySelectorAll('.js-load-more-grid').forEach(function (grid) {
    var cards = Array.prototype.slice.call(grid.children);
    if (cards.length <= PAGE_SIZE) return;

    cards.forEach(function (card, i) {
      card.style.display = i < PAGE_SIZE ? '' : 'none';
    });

    var visibleCount = PAGE_SIZE;

    var wrap = document.createElement('div');
    wrap.className = 'load-more-wrap';
    var btn = document.createElement('button');
    btn.className = 'btn-load-more';
    btn.type = 'button';
    btn.textContent = 'Carregar mais';
    wrap.appendChild(btn);
    grid.insertAdjacentElement('afterend', wrap);

    btn.addEventListener('click', function () {
      var next = cards.slice(visibleCount, visibleCount + PAGE_SIZE);
      next.forEach(function (card) { card.style.display = ''; });
      visibleCount += next.length;
      if (visibleCount >= cards.length) {
        wrap.style.display = 'none';
      }
    });
  });
})();
