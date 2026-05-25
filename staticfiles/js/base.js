const flagIcon = document.getElementById("flagIcon");
const userPopup = document.getElementById("userPopup");
const logoutBtn = document.getElementById("logoutBtn");
const themeButton = document.getElementById("themeButton");

// ---------- USER POPUP ----------
flagIcon.addEventListener("click", () => {
  userPopup.style.display =
    userPopup.style.display === "block" ? "none" : "block";
});

logoutBtn.addEventListener("click", () => {
  userPopup.style.display = "block";
  setTimeout(() => {
    window.location.href = logoutUrl; // from base.html
  }, 1000);
});

document.addEventListener("click", (e) => {
  if (!e.target.closest(".user-flag-container")) {
    userPopup.style.display = "none";
  }
});

// ---------- THEME MANAGEMENT ----------
function updateTheme(theme) {
  document.documentElement.setAttribute("data-theme", theme);
  localStorage.setItem("theme", theme);
  themeButton.textContent = theme === "dark" ? "☀️" : "🌙";
}

const savedTheme = localStorage.getItem("theme") || "light";
updateTheme(savedTheme);

themeButton.addEventListener("click", () => {
  const current = document.documentElement.getAttribute("data-theme");
  const newTheme = current === "dark" ? "light" : "dark";
  updateTheme(newTheme);
});
