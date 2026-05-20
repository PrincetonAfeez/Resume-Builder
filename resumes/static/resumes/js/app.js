(function () {
  function getCookie(name) {
    const value = "; " + document.cookie;
    const parts = value.split("; " + name + "=");
    if (parts.length === 2) {
      return parts.pop().split(";").shift();
    }
    return undefined;
  }

  document.body.addEventListener("htmx:configRequest", function (event) {
    const token = getCookie("csrftoken");
    if (token) {
      event.detail.headers["X-CSRFToken"] = token;
    }
  });

  function setSavedIndicator(text, activeClass) {
    const indicator = document.querySelector("#saved-indicator");
    if (!indicator) {
      return;
    }
    indicator.textContent = text;
    indicator.classList.remove("text-slate-400", "text-emerald-700", "text-amber-700");
    indicator.classList.add(activeClass);
    window.setTimeout(function () {
      indicator.textContent = "Idle";
      indicator.classList.add("text-slate-400");
      indicator.classList.remove(activeClass);
    }, 1800);
  }

  document.body.addEventListener("resume:saved", function () {
    setSavedIndicator("Saved", "text-emerald-700");
  });

  document.body.addEventListener("resume:invalid", function () {
    setSavedIndicator("Not saved", "text-amber-700");
  });

  function refreshIcons() {
    if (window.lucide) {
      window.lucide.createIcons();
    }
  }

  document.body.addEventListener("htmx:afterSettle", refreshIcons);
  refreshIcons();
})();
