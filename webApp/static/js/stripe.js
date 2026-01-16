// Frontend helpers for Stripe Checkout.
// Stripe.js v3 is loaded globally in `templates/base.html`.

(function () {
  function byId(id) {
    return document.getElementById(id);
  }

  function showError(el, message) {
    if (!el) return;
    el.textContent = message || "Something went wrong. Please try again.";
    el.style.display = "block";
  }

  async function postJson(url, payload) {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload || {})
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      const msg = data && (data.error || data.message);
      throw new Error(msg || `Request failed (${res.status})`);
    }
    return data;
  }

  function setupLandingCheckout(opts) {
    const form = byId(opts.formId);
    const select = byId(opts.packageSelectId);
    const qtyInput = byId(opts.quantityInputId);
    const errorEl = byId(opts.errorId);
    const createCheckoutUrl = opts.createCheckoutUrl;

    if (!form || !select || !qtyInput || !createCheckoutUrl) return;

    form.addEventListener("submit", async function (e) {
      e.preventDefault();
      if (errorEl) errorEl.style.display = "none";

      const packageId = select.value;
      const qtyRaw = qtyInput.value;
      const quantity = Math.max(1, Math.min(99, parseInt(qtyRaw || "1", 10) || 1));

      try {
        const payload = {
          package_id: packageId,
          quantity: quantity
        };

        // Optional (server will create if missing)
        if (window.__SPACEGAME_PLAYER_UUID__) {
          payload.player_uuid = window.__SPACEGAME_PLAYER_UUID__;
        }

        const data = await postJson(createCheckoutUrl, payload);
        if (data.url) {
          window.location.href = data.url;
          return;
        }

        // Fallback if you later switch to redirectToCheckout usage.
        showError(errorEl, "Checkout URL missing from server response.");
      } catch (err) {
        showError(errorEl, err && err.message ? err.message : String(err));
      }
    });
  }

  window.SpaceGameStripe = window.SpaceGameStripe || {};
  window.SpaceGameStripe.setupLandingCheckout = setupLandingCheckout;
})();
