// ---------- Load Header ----------
function loadHeader() {
  fetch('header.html')
    .then(response => response.text())
    .then(data => {
      document.getElementById('header').innerHTML = data;
      initHeaderScripts(); // Attach menu and scroll after header loads
    });
}

// ---------- Load Footer ----------
function loadFooter() {
  fetch('footer.html')
    .then(response => response.text())
    .then(data => {
      document.getElementById('footer').innerHTML = data;
    });
}

// ---------- Initialize header scripts ----------
function initHeaderScripts() {
  const mobileBtn = document.getElementById('mobileMenuBtn');
  const mainNav = document.getElementById('mainNav');

  // Mobile menu toggle
  if (mobileBtn && mainNav) {
    mobileBtn.addEventListener('click', () => {
      mainNav.classList.toggle('active');
      mobileBtn.innerHTML = 
      mainNav.classList.contains('active') ? 
      `<i class="fas fa-times"></i>` : `<i class="fas fa-bars"></i>`;
    });
  }

  // Smooth scrolling for anchor links inside header
  const navLinks = document.querySelectorAll('#mainNav a[href^="#"]');
  navLinks.forEach(anchor => {
    anchor.addEventListener('click', e => {
      e.preventDefault();
      const targetId = anchor.getAttribute('href');
      if (targetId === '#') return;

      const targetElement = document.querySelector(targetId);
      if (targetElement) {
        window.scrollTo({
          top: targetElement.offsetTop - 80,
          behavior: 'smooth'
        });

        // Close mobile menu if open
        if (mainNav.classList.contains('active')) {
          mainNav.classList.remove('active');
        }
      }
    });
  });
}

// ---------- Initialize all ----------
document.addEventListener('DOMContentLoaded', () => {
  loadHeader();
  loadFooter();
});
