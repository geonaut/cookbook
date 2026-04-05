// Foodie map — tab switching and map zoom
(function () {
  var container = document.querySelector('.foodie-container');
  if (!container) return;

  var mapId = container.dataset.mapId;

  function openCategory(catId, activeBtn) {
    container.querySelectorAll('.tab-content').forEach(function (el) { el.style.display = 'none'; });
    container.querySelectorAll('.tab-btn').forEach(function (el) { el.classList.remove('active'); });
    var panel = document.getElementById(catId);
    if (panel) panel.style.display = 'block';
    if (activeBtn) activeBtn.classList.add('active');
  }

  function zoomTo(lat, lon) {
    if (!lat || lat === '0') return;
    var iframe = document.getElementById('main-foodie-map');
    if (!iframe) return;
    iframe.src = 'https://www.google.com/maps/d/embed?mid=' + mapId + '&ll=' + lat + '%2C' + lon + '&z=18';
  }

  // Event delegation — no inline onclick needed
  container.addEventListener('click', function (e) {
    var tabBtn = e.target.closest('[data-cat-id]');
    if (tabBtn) { openCategory(tabBtn.dataset.catId, tabBtn); return; }

    var locCard = e.target.closest('[data-lat]');
    if (locCard) { zoomTo(locCard.dataset.lat, locCard.dataset.lon); }
  });

  // Activate first tab on load
  var firstTab = container.querySelector('[data-cat-id]');
  if (firstTab) openCategory(firstTab.dataset.catId, firstTab);
}());
