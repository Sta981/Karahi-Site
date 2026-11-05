// Confirm before destructive admin actions (forms with data-confirm).
document.addEventListener("submit", function (event) {
  var message = event.target.getAttribute("data-confirm");
  if (message && !window.confirm(message)) {
    event.preventDefault();
  }
});

// The navigation remains available without JavaScript via its noscript fallback.
var navToggle = document.querySelector(".nav-toggle");
var navigation = document.getElementById("site-navigation");
function closeNavigation() {
  navigation.classList.remove("is-open");
  navToggle.setAttribute("aria-expanded", "false");
  navToggle.setAttribute("aria-label", "Open navigation");
}
if (navToggle && navigation) {
  navToggle.addEventListener("click", function () {
    var expanded = navToggle.getAttribute("aria-expanded") !== "true";
    navigation.classList.toggle("is-open", expanded);
    navToggle.setAttribute("aria-expanded", String(expanded));
    navToggle.setAttribute("aria-label", expanded ? "Close navigation" : "Open navigation");
  });
  document.addEventListener("click", function (event) {
    if (!navigation.contains(event.target) && !navToggle.contains(event.target)) closeNavigation();
  });
  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && navToggle.getAttribute("aria-expanded") === "true") {
      closeNavigation();
      navToggle.focus();
    }
  });
}

// Highlight the category currently being browsed, including keyboard navigation.
var tabs = Array.from(document.querySelectorAll(".category-tab"));
function markCategory(id) {
  tabs.forEach(function (tab) {
    var active = tab.hash === "#" + id;
    tab.classList.toggle("active", active);
    if (active) tab.setAttribute("aria-current", "location");
    else tab.removeAttribute("aria-current");
  });
}
tabs.forEach(function (tab) {
  tab.addEventListener("click", function () { markCategory(tab.hash.slice(1)); });
});
if ("IntersectionObserver" in window) {
  var observer = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (entry.isIntersecting) markCategory(entry.target.id);
    });
  }, {rootMargin: "-70px 0px -60% 0px", threshold: 0});
  document.querySelectorAll(".menu-section").forEach(function (section) { observer.observe(section); });
}
