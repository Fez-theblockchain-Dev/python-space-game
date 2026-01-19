// Frontend helpers for Stripe Checkout.
// Stripe.js v3 is loaded globally in `templates/base.html`.
//
// API Endpoints used:
// - POST /api/create-checkout-session/  -> Creates Stripe hosted checkout
// - POST /api/create-payment-intent/    -> Creates PaymentIntent for Express Checkout (Apple Pay)
// - POST /api/stripe-webhook/           -> Webhook handler for Stripe events
// - GET  /payment/success/              -> Success redirect page
// - GET  /payment/cancelled/            -> Cancelled redirect page

(function () {
  function byId(id) {
    return document.getElementById(id);
  }

  function showError(el, message) {
    const msg = message || "Something went wrong. Please try again.";
    if (!el) {
      window.alert(msg);
      return;
    }
    el.textContent = msg;
    el.style.display = "block";
  }

  function hideError(el) {
    if (el) el.style.display = "none";
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

  /**
   * Setup checkout for a single package select dropdown.
   * @param {Object} opts - Configuration options
   * @param {string} opts.formId - Form element ID
   * @param {string} opts.packageSelectId - Package select element ID
   * @param {string} opts.quantityInputId - Quantity input element ID
   * @param {string} opts.errorId - Error display element ID
   * @param {string} opts.createCheckoutUrl - API endpoint for creating checkout session
   */
  function setupLandingCheckout(opts) {
    const form = byId(opts.formId);
    const select = byId(opts.packageSelectId);
    const qtyInput = byId(opts.quantityInputId);
    const errorEl = byId(opts.errorId);
    const createCheckoutUrl = opts.createCheckoutUrl;

    if (!form || !select || !qtyInput || !createCheckoutUrl) return;

    form.addEventListener("submit", async function (e) {
      e.preventDefault();
      hideError(errorEl);

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

        showError(errorEl, "Checkout URL missing from server response.");
      } catch (err) {
        showError(errorEl, err && err.message ? err.message : String(err));
      }
    });
  }

  /**
   * Setup checkout for dual-select form (Gold Coins + Health Packs).
   * This form allows users to select packages from two categories.
   * @param {Object} opts - Configuration options
   * @param {string} opts.formId - Form element ID
   * @param {string} opts.goldSelectId - Gold coins select element ID
   * @param {string} opts.healthSelectId - Health packs select element ID
   * @param {string} opts.quantityInputId - Quantity input element ID
   * @param {string} opts.errorId - Error display element ID
   * @param {string} opts.createCheckoutUrl - API endpoint: /api/create-checkout-session/
   */
  function setupDualSelectCheckout(opts) {
    const form = byId(opts.formId);
    const goldSelect = byId(opts.goldSelectId);
    const healthSelect = byId(opts.healthSelectId);
    const qtyInput = byId(opts.quantityInputId);
    const errorEl = byId(opts.errorId);
    const createCheckoutUrl = opts.createCheckoutUrl;

    if (!form || !createCheckoutUrl) return;

    form.addEventListener("submit", async function (e) {
      e.preventDefault();
      hideError(errorEl);

      const qtyRaw = qtyInput ? qtyInput.value : "1";
      const quantity = Math.max(1, Math.min(99, parseInt(qtyRaw || "1", 10) || 1));

      // Build items array from selections
      const items = [];
      
      if (goldSelect && goldSelect.value) {
        items.push({ id: goldSelect.value, quantity: quantity });
      }
      
      if (healthSelect && healthSelect.value) {
        items.push({ id: healthSelect.value, quantity: quantity });
      }

      if (items.length === 0) {
        showError(errorEl, "Please select at least one package.");
        return;
      }

      try {
        const payload = { items: items };

        if (window.__SPACEGAME_PLAYER_UUID__) {
          payload.player_uuid = window.__SPACEGAME_PLAYER_UUID__;
        }

        const data = await postJson(createCheckoutUrl, payload);
        if (data.url) {
          window.location.href = data.url;
          return;
        }

        showError(errorEl, "Checkout URL missing from server response.");
      } catch (err) {
        showError(errorEl, err && err.message ? err.message : String(err));
      }
    });
  }

  /**
   * Setup checkout buttons for individual package cards.
   * @param {Object} opts - Configuration options
   * @param {string} opts.buttonSelector - CSS selector for buy buttons
   * @param {string} opts.errorId - Error display element ID
   * @param {string} opts.createCheckoutUrl - API endpoint: /api/create-checkout-session/
   */
  function setupPackageCheckout(opts) {
    const buttons = document.querySelectorAll(opts.buttonSelector || "");
    const errorEl = opts.errorId ? byId(opts.errorId) : null;
    const createCheckoutUrl = opts.createCheckoutUrl;

    if (!buttons.length || !createCheckoutUrl) return;

    buttons.forEach(function (button) {
      button.addEventListener("click", async function (e) {
        e.preventDefault();
        hideError(errorEl);

        const packageId = button.getAttribute("data-package-id");
        if (!packageId) {
          showError(errorEl, "Package is missing.");
          return;
        }

        // Disable button during request
        button.disabled = true;
        const originalText = button.textContent;
        button.textContent = "Processing...";

        const payload = {
          package_id: packageId,
          quantity: 1
        };

        if (window.__SPACEGAME_PLAYER_UUID__) {
          payload.player_uuid = window.__SPACEGAME_PLAYER_UUID__;
        }

        try {
          const data = await postJson(createCheckoutUrl, payload);
          if (data.url) {
            window.location.href = data.url;
            return;
          }
          showError(errorEl, "Checkout URL missing from server response.");
        } catch (err) {
          showError(errorEl, err && err.message ? err.message : String(err));
        } finally {
          button.disabled = false;
          button.textContent = originalText;
        }
      });
    });
  }

  /**
   * Setup Express Checkout Element for Apple Pay / Google Pay.
   * Uses PaymentIntent API for direct payment without redirect.
   * @param {Object} opts - Configuration options
   * @param {string} opts.containerId - Container element ID for Express Checkout
   * @param {string} opts.packageId - Package ID to purchase
   * @param {string} opts.createPaymentIntentUrl - API endpoint: /api/create-payment-intent/
   * @param {string} opts.successUrl - URL to redirect on success
   */
  function setupExpressCheckout(opts) {
    const container = byId(opts.containerId);
    const publishableKey = window.__SPACEGAME_STRIPE_PUBLISHABLE_KEY__;
    
    if (!container || !publishableKey || !opts.packageId) return;

    const stripe = Stripe(publishableKey);

    async function initExpressCheckout() {
      try {
        // Create PaymentIntent to get client secret
        const payload = {
          package_id: opts.packageId
        };

        if (window.__SPACEGAME_PLAYER_UUID__) {
          payload.player_uuid = window.__SPACEGAME_PLAYER_UUID__;
        }

        const intentData = await postJson(opts.createPaymentIntentUrl, payload);
        
        if (!intentData.clientSecret) {
          console.error("No client secret returned");
          return;
        }

        // Create Elements instance
        const elements = stripe.elements({
          clientSecret: intentData.clientSecret,
        });

        // Create Express Checkout Element
        const expressCheckoutElement = elements.create("expressCheckout", {
          buttonType: {
            applePay: "buy",
            googlePay: "buy",
          },
        });

        expressCheckoutElement.mount("#" + opts.containerId);

        expressCheckoutElement.on("confirm", async function (event) {
          const { error } = await stripe.confirmPayment({
            elements,
            confirmParams: {
              return_url: opts.successUrl || window.location.origin + "/payment/success/",
            },
          });

          if (error) {
            console.error("Payment error:", error.message);
          }
        });

      } catch (err) {
        console.error("Express checkout setup failed:", err);
      }
    }

    initExpressCheckout();
  }

  /**
   * Fetch and display player wallet balance.
   * @param {Object} opts - Configuration options
   * @param {string} opts.walletUrl - API endpoint for wallet data
   * @param {string} opts.goldDisplayId - Element ID to display gold coins
   * @param {string} opts.healthDisplayId - Element ID to display health packs
   */
  function setupWalletDisplay(opts) {
    const goldEl = byId(opts.goldDisplayId);
    const healthEl = byId(opts.healthDisplayId);
    const walletUrl = opts.walletUrl;

    if (!walletUrl || (!goldEl && !healthEl)) return;

    async function fetchWallet() {
      try {
        const playerUuid = window.__SPACEGAME_PLAYER_UUID__;
        if (!playerUuid) return;

        const res = await fetch(walletUrl + "?player_uuid=" + encodeURIComponent(playerUuid));
        if (!res.ok) return;

        const data = await res.json();
        if (goldEl && data.gold_coins !== undefined) {
          goldEl.textContent = data.gold_coins.toLocaleString();
        }
        if (healthEl && data.health_packs !== undefined) {
          healthEl.textContent = data.health_packs.toLocaleString();
        }
      } catch (err) {
        console.error("Failed to fetch wallet:", err);
      }
    }

    fetchWallet();
  }

  // Export functions to global namespace
  window.SpaceGameStripe = window.SpaceGameStripe || {};
  window.SpaceGameStripe.setupLandingCheckout = setupLandingCheckout;
  window.SpaceGameStripe.setupDualSelectCheckout = setupDualSelectCheckout;
  window.SpaceGameStripe.setupPackageCheckout = setupPackageCheckout;
  window.SpaceGameStripe.setupExpressCheckout = setupExpressCheckout;
  window.SpaceGameStripe.setupWalletDisplay = setupWalletDisplay;
})();
