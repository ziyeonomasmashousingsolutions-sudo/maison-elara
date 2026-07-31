// Maison Elara — global front-end behaviour (vanilla JS, no dependencies)

document.addEventListener('DOMContentLoaded', function () {

  // ---- Mobile nav toggle -------------------------------------------------
  var navToggle = document.querySelector('.nav-toggle');
  var navBar = document.querySelector('.nav-bar');
  if (navToggle && navBar) {
    navToggle.addEventListener('click', function () {
      navBar.classList.toggle('open');
    });
  }

  // ---- Auto-dismiss flash messages --------------------------------------
  document.querySelectorAll('.flash').forEach(function (el) {
    setTimeout(function () {
      el.style.transition = 'opacity 0.4s ease';
      el.style.opacity = '0';
      setTimeout(function () { el.remove(); }, 400);
    }, 3500);
  });

  // ---- Product gallery (thumbnail swap) ---------------------------------
  var mainImage = document.querySelector('[data-gallery-main]');
  var thumbs = document.querySelectorAll('[data-gallery-thumb]');
  thumbs.forEach(function (thumb) {
    thumb.addEventListener('click', function () {
      if (!mainImage) return;
      mainImage.src = thumb.dataset.full || thumb.src;
      thumbs.forEach(function (t) { t.classList.remove('active'); });
      thumb.classList.add('active');
    });
  });

  // ---- Size / colour swatch selection ------------------------------------
  document.querySelectorAll('[data-swatch-group]').forEach(function (group) {
    var buttons = group.querySelectorAll('.swatch');
    var hiddenInput = document.querySelector('#' + group.dataset.swatchGroup);
    buttons.forEach(function (btn, index) {
      if (index === 0) {
        btn.classList.add('selected');
        if (hiddenInput) hiddenInput.value = btn.dataset.value;
      }
      btn.addEventListener('click', function () {
        buttons.forEach(function (b) { b.classList.remove('selected'); });
        btn.classList.add('selected');
        if (hiddenInput) hiddenInput.value = btn.dataset.value;
      });
    });
  });

  // ---- Quantity stepper (product page) -----------------------------------
  document.querySelectorAll('[data-qty-stepper]').forEach(function (stepper) {
    var input = stepper.querySelector('input');
    var minus = stepper.querySelector('[data-qty-minus]');
    var plus = stepper.querySelector('[data-qty-plus]');
    if (minus) minus.addEventListener('click', function () {
      var val = Math.max(1, parseInt(input.value || '1', 10) - 1);
      input.value = val;
    });
    if (plus) plus.addEventListener('click', function () {
      var val = parseInt(input.value || '1', 10) + 1;
      input.value = val;
    });
  });

});
