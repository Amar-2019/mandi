// Theme toggle
const themeButton = document.getElementById("themeButton");
const currentTheme = localStorage.getItem("theme") || "light";

function updateTheme(theme) {
  document.documentElement.setAttribute("data-theme", theme);
  localStorage.setItem("theme", theme);
  if (theme === "dark") {
    themeButton.textContent = "🌙";
    themeButton.className = "theme-toggle moon";
  } else {
    themeButton.textContent = "☀️";
    themeButton.className = "theme-toggle sun";
  }
}

updateTheme(currentTheme);

themeButton.addEventListener("click", () => {
  const newTheme = document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark";
  updateTheme(newTheme);
});

// Toggle password visibility
function togglePassword() {
  const passwordField = document.getElementById("password");
  const toggle = document.querySelector(".toggle-password");
  passwordField.type = passwordField.type === "password" ? "text" : "password";
  toggle.classList.toggle("active");
}

// Popup auto-hide
window.onload = () => {
  const popup = document.getElementById("popup");
  if (popup) setTimeout(() => { popup.style.display = "none"; }, 3000);
};

// Particle background
const canvas = document.getElementById('bgCanvas');
const ctx = canvas.getContext('2d');
canvas.width = window.innerWidth;
canvas.height = window.innerHeight;

const particles = [];
for (let i = 0; i < 120; i++) {
  particles.push({
    x: Math.random() * canvas.width,
    y: Math.random() * canvas.height,
    r: Math.random() * 2 + 1,
    dx: (Math.random() - 0.5) / 2,
    dy: (Math.random() - 0.5) / 2
  });
}

function animateParticles() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  for (let p of particles) {
    ctx.beginPath();
    ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(0,0,0,0.05)';
    ctx.fill();
    p.x += p.dx;
    p.y += p.dy;
    if (p.x < 0 || p.x > canvas.width) p.dx *= -1;
    if (p.y < 0 || p.y > canvas.height) p.dy *= -1;
  }
  requestAnimationFrame(animateParticles);
}
animateParticles();

window.addEventListener('resize', () => {
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
});
