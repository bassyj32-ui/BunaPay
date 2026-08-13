/* BunaPay Mini App — order form.
 * Opened from the bot via a WebApp button; data is returned to the bot with
 * Telegram.WebApp.sendData(). The bot re-validates everything server-side.
 */
(function () {
  "use strict";

  var tg = (window.Telegram && window.Telegram.WebApp) || null;

  // ---------- payload from the bot (?d=<urlencoded JSON>) ----------
  function parsePayload() {
    try {
      var raw = new URLSearchParams(window.location.search).get("d");
      if (!raw) return null;
      return JSON.parse(decodeURIComponent(raw));
    } catch (e) {
      return null;
    }
  }
  var payload = parsePayload();
  var RATE = payload && typeof payload.r === "number" ? payload.r : null;
  var SERVICES = (payload && Array.isArray(payload.s) && payload.s) || [];
  var MIN = (payload && payload.min) || 5;
  var MAX = (payload && payload.max) || 100;
  var PRESETS = [10, 20, 50, 100];

  // ---------- theme ----------
  if (tg && tg.themeParams) {
    var t = tg.themeParams;
    var set = function (name, value) {
      if (value) document.documentElement.style.setProperty(name, value);
    };
    set("--bg", t.bg_color);
    set("--text", t.text_color);
    set("--hint", t.hint_color);
    set("--secondary-bg", t.secondary_bg_color);
    set("--button", t.button_color);
    set("--button-text", t.button_text_color);
    set("--border", t.secondary_bg_color || null);
    if (t.section_bg_color) set("--secondary-bg", t.section_bg_color);
  }
  if (tg) {
    tg.ready();
    tg.expand();
    tg.setHeaderColor && tg.setHeaderColor(tg.themeParams && tg.themeParams.bg_color ? tg.themeParams.bg_color : "#ffffff");
  }

  // ---------- state ----------
  var state = { service: null, amount: null, wallet: "" };

  // ---------- dom ----------
  var $ = function (id) { return document.getElementById(id); };
  var rateLine = $("rate-line");
  var serviceGrid = $("service-grid");
  var serviceSection = $("service-section");
  var amountSection = $("amount-section");
  var amountChips = $("amount-chips");
  var customAmount = $("custom-amount");
  var amountSummary = $("amount-summary");
  var walletSection = $("wallet-section");
  var walletInput = $("wallet");
  var submitBtn = $("submit");
  var errorEl = $("error");
  var devNote = $("dev-note");

  function showError(msg) {
    errorEl.textContent = msg;
    errorEl.hidden = false;
  }
  function clearError() {
    errorEl.hidden = true;
  }

  function fmt(n) {
    return (Math.round(n * 100) / 100).toString();
  }

  // ---------- rate ----------
  if (RATE !== null) {
    rateLine.textContent = "1 USDT = " + fmt(RATE) + " ETB";
  } else {
    rateLine.textContent = "Rates are being updated — try again shortly.";
  }

  // ---------- services ----------
  function renderServices() {
    serviceGrid.innerHTML = "";
    SERVICES.forEach(function (s) {
      var tile = document.createElement("button");
      tile.type = "button";
      tile.className = "tile";
      tile.innerHTML =
        '<span class="name"></span><span class="price"></span>';
      tile.querySelector(".name").textContent = s.n;
      tile.querySelector(".price").textContent = s.p + " USDT";
      tile.addEventListener("click", function () {
        state.service = s.i;
        state.amount = Number(s.p);
        document.querySelectorAll(".tile").forEach(function (el) {
          el.classList.remove("selected");
        });
        tile.classList.add("selected");
        selectServiceMode(false);
      });
      serviceGrid.appendChild(tile);
    });

    // "Other amount" tile — no service, free amount.
    var other = document.createElement("button");
    other.type = "button";
    other.className = "tile";
    other.innerHTML = '<span class="name">Other amount</span><span class="price">Custom USDT</span>';
    other.addEventListener("click", function () {
      state.service = null;
      document.querySelectorAll(".tile").forEach(function (el) {
        el.classList.remove("selected");
      });
      other.classList.add("selected");
      selectServiceMode(true);
    });
    serviceGrid.appendChild(other);

    if (SERVICES.length === 0) {
      selectServiceMode(true); // nothing offered — free amount
    }
  }

  function selectServiceMode(isCustom) {
    clearError();
    amountSection.hidden = false;
    walletSection.hidden = false;
    renderAmounts(isCustom);
    updateSubmit();
  }

  // ---------- amount ----------
  function renderAmounts(isCustom) {
    amountChips.innerHTML = "";
    PRESETS.forEach(function (p) {
      var chip = document.createElement("button");
      chip.type = "button";
      chip.className = "chip";
      chip.textContent = p + " USDT";
      chip.addEventListener("click", function () {
        state.amount = p;
        customAmount.hidden = true;
        customAmount.value = "";
        document.querySelectorAll(".chip").forEach(function (el) {
          el.classList.remove("selected");
        });
        chip.classList.add("selected");
        clearError();
        updateSubmit();
      });
      amountChips.appendChild(chip);
    });

    var prefill = isCustom ? null : state.amount;
    if (prefill !== null && prefill !== undefined) {
      // prefill custom input if the price isn't one of the presets
      if (PRESETS.indexOf(prefill) === -1) {
        customAmount.hidden = false;
        customAmount.value = prefill;
        state.amount = prefill;
        customAmount.focus();
      } else {
        customAmount.hidden = true;
        customAmount.value = "";
      }
    } else {
      customAmount.hidden = !isCustom;
    }
    updateAmountSummary();
    updateSubmit();
  }

  customAmount.addEventListener("input", function () {
    var v = parseFloat(customAmount.value);
    state.amount = isNaN(v) ? null : v;
    clearError();
    updateAmountSummary();
    updateSubmit();
  });

  function updateAmountSummary() {
    if (state.amount !== null && RATE !== null) {
      amountSummary.hidden = false;
      amountSummary.textContent = state.amount + " USDT ≈ " + fmt(state.amount * RATE) + " ETB";
    } else {
      amountSummary.hidden = true;
    }
  }

  // ---------- wallet ----------
  walletInput.addEventListener("input", function () {
    state.wallet = walletInput.value.trim();
    clearError();
    updateSubmit();
  });

  // ---------- validation ----------
  function validate() {
    if (state.amount === null || isNaN(state.amount)) {
      return "Enter an amount in USDT.";
    }
    if (state.amount < MIN || state.amount > MAX) {
      return "Amount must be between " + MIN + " and " + MAX + " USDT.";
    }
    if (!/^0x[a-fA-F0-9]{40}$/.test(state.wallet)) {
      return "Enter a valid BSC address: 0x followed by 40 hex characters.";
    }
    return null;
  }

  function updateSubmit() {
    submitBtn.disabled = RATE === null || validate() !== null;
  }

  // ---------- submit ----------
  submitBtn.addEventListener("click", function () {
    var err = validate();
    if (err) {
      showError(err);
      return;
    }
    if (!tg || typeof tg.sendData !== "function") {
      showError("Open this app from the Telegram bot to place an order.");
      return;
    }
    var data = JSON.stringify({
      service: state.service,
      usdt: Number(fmt(state.amount)),
      wallet: state.wallet,
    });
    tg.sendData(data);
  });

  // ---------- init ----------
  if (!tg) {
    devNote.hidden = false;
  }
  renderServices();
  updateSubmit();
})();
