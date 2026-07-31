// Maison Elara — cart page behaviour
// Each cart row has its own small form; we just adjust the number input
// locally, then let the existing "Update" button submit it to the server,
// which recalculates totals. Kept intentionally simple and dependency-free.

document.addEventListener('DOMContentLoaded', function () {
  document.querySelectorAll('[data-cart-qty]').forEach(function (wrapper) {
    var input = wrapper.querySelector('input[type="number"]');
    var minus = wrapper.querySelector('[data-cart-minus]');
    var plus = wrapper.querySelector('[data-cart-plus]');

    if (minus) {
      minus.addEventListener('click', function () {
        var val = Math.max(0, parseInt(input.value || '1', 10) - 1);
        input.value = val;
        wrapper.closest('form').requestSubmit();
      });
    }
    if (plus) {
      plus.addEventListener('click', function () {
        var val = parseInt(input.value || '1', 10) + 1;
        input.value = val;
        wrapper.closest('form').requestSubmit();
      });
    }
  });
});
