(function () {
  var PAGE_SIZE = 12;
  var grid = document.getElementById('promocoes-grid');
  var btn = document.getElementById('load-more-btn');
  if (!grid) return;

  var cards = Array.prototype.slice.call(grid.querySelectorAll('.card'));
  if (cards.length === 0) return;

  cards.forEach(function (card, i) {
    card.style.display = i < PAGE_SIZE ? '' : 'none';
  });

  var visibleCount = Math.min(PAGE_SIZE, cards.length);

  if (!btn) return;

  if (visibleCount >= cards.length) {
    btn.style.display = 'none';
  }

  btn.addEventListener('click', function () {
    var next = cards.slice(visibleCount, visibleCount + PAGE_SIZE);
    next.forEach(function (card) {
      card.style.display = '';
    });
    visibleCount += next.length;
    if (visibleCount >= cards.length) {
      btn.style.display = 'none';
    }
  });
})();
