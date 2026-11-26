/**
 * RestroIQ Enterprise Frontend Scripts
 * Micro-interactions, Theme Switcher, and Real-time Navigation
 */

document.addEventListener("DOMContentLoaded", () => {
  // 1. Dark Mode State Management
  const themeToggle = document.getElementById("theme-toggle");
  const savedTheme = localStorage.getItem("restroiq-theme");
  
  if (savedTheme === "dark" || (!savedTheme && window.matchMedia("(prefers-color-scheme: dark)").matches)) {
    document.body.classList.add("dark");
  }
  
  if (themeToggle) {
    themeToggle.addEventListener("click", () => {
      document.body.classList.toggle("dark");
      const isDark = document.body.classList.contains("dark");
      localStorage.setItem("restroiq-theme", isDark ? "dark" : "light");
    });
  }

  // 2. Mobile Sidebar Toggle
  const sidebarToggle = document.getElementById("sidebar-toggle");
  if (sidebarToggle) {
    sidebarToggle.addEventListener("click", () => {
      document.body.classList.toggle("sidebar-open");
    });
  }

  // Close sidebar on background click for mobile
  document.addEventListener("click", (e) => {
    if (document.body.classList.contains("sidebar-open")) {
      const sidebar = document.getElementById("sidebar");
      if (sidebar && !sidebar.contains(e.target) && !sidebarToggle.contains(e.target)) {
        document.body.classList.remove("sidebar-open");
      }
    }
  });

  // 3. Pill Toggle Groups (Monthly / Yearly / Daily)
  const pillGroups = document.querySelectorAll(".pill-toggle-group");
  pillGroups.forEach(group => {
    const buttons = group.querySelectorAll(".pill-btn");
    buttons.forEach(btn => {
      btn.addEventListener("click", () => {
        buttons.forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
      });
    });
  });

  // 4. Client-side Real-time Global Search
  const globalSearch = document.getElementById("global-search");
  if (globalSearch) {
    globalSearch.addEventListener("input", (e) => {
      const term = e.target.value.toLowerCase().trim();
      const rows = document.querySelectorAll(".restroiq-table tbody tr, .directory-grid .directory-card, .staff-profile-card");
      
      rows.forEach(row => {
        const text = row.innerText.toLowerCase();
        if (text.includes(term)) {
          row.style.display = "";
        } else {
          row.style.display = "none";
        }
      });
    });
  }

  // 5. Flash message auto-dismiss after 6 seconds
  const flashAlerts = document.querySelectorAll(".flash-alert");
  flashAlerts.forEach(alert => {
    setTimeout(() => {
      alert.style.transition = "opacity 0.4s ease";
      alert.style.opacity = "0";
      setTimeout(() => alert.remove(), 400);
    }, 6000);
  });
});
