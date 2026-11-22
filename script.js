(() => {
  'use strict';

  const toggle = document.querySelector('.nav-toggle');
  const links = document.getElementById('nav-links');

  if (toggle && links) {
    toggle.addEventListener('click', () => {
      const open = toggle.getAttribute('aria-expanded') === 'true';
      toggle.setAttribute('aria-expanded', String(!open));
      links.classList.toggle('open', !open);
    });

    links.addEventListener('click', (event) => {
      if (event.target.closest('a')) {
        toggle.setAttribute('aria-expanded', 'false');
        links.classList.remove('open');
      }
    });
  }

  const cards = document.querySelectorAll('.credit-card');
  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry, index) => {
        if (!entry.isIntersecting) return;
        entry.target.style.transitionDelay = (index % 3) * 70 + 'ms';
        entry.target.classList.add('visible');
        observer.unobserve(entry.target);
      });
    }, { threshold: 0.15 });

    cards.forEach((card) => {
      card.classList.add('reveal');
      observer.observe(card);
    });
  }

  const creditsLink = document.querySelector('.nav-links a[href="#credits"]');
  const credits = document.getElementById('credits');
  if (creditsLink && credits && 'IntersectionObserver' in window) {
    const sectionObserver = new IntersectionObserver((entries) => {
      entries.forEach((entry) => creditsLink.classList.toggle('active', entry.isIntersecting));
    }, { rootMargin: '-45% 0px -50% 0px' });
    sectionObserver.observe(credits);
  }
})();
