(function () {
  var saved = localStorage.getItem('decima-theme');
  if (saved === 'dark') {
    document.documentElement.setAttribute('data-theme', 'dark');
  }

  window.toggleTheme = function () {
    var html = document.documentElement;
    var isDark = html.getAttribute('data-theme') === 'dark';
    if (isDark) {
      html.removeAttribute('data-theme');
      localStorage.setItem('decima-theme', 'light');
    } else {
      html.setAttribute('data-theme', 'dark');
      localStorage.setItem('decima-theme', 'dark');
    }
  };
})();
