/* StudyAI landing — icons, scroll reveal, FAQ accordion, language switch.
   Language is server-rendered (Django i18n), but instead of a hard reload we
   set the language cookie, re-fetch the page in the new language, and swap the
   #page content with a soft fade — no navigation, no flash, scroll preserved.
   Falls back to a full reload on any error; the <form>s work without JS too. */

function initIcons() {
  if (window.lucide) lucide.createIcons();
}

function initReveal() {
  const io = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if (e.isIntersecting) { e.target.classList.add('show'); io.unobserve(e.target); }
    });
  }, { threshold: 0.12 });
  document.querySelectorAll('.reveal:not(.show)').forEach(el => io.observe(el));
}

function initFaq() {
  document.querySelectorAll('.qa-q').forEach(btn => {
    btn.addEventListener('click', () => {
      const qa = btn.closest('.qa');
      const a = qa.querySelector('.qa-a');
      if (qa.classList.contains('open')) { qa.classList.remove('open'); a.style.maxHeight = '0'; }
      else { qa.classList.add('open'); a.style.maxHeight = a.scrollHeight + 'px'; }
    });
  });
}

function initLangSwitch() {
  const sw = document.querySelector('.lang-switch');
  if (!sw) return;
  const slider = sw.querySelector('.lang-slider');
  const buttons = Array.from(sw.querySelectorAll('button'));
  const active = () => sw.querySelector('button.on') || buttons[0];

  function place(btn, animate) {
    if (!slider || !btn) return;
    if (!animate) slider.style.transition = 'none';
    const a = sw.getBoundingClientRect(), b = btn.getBoundingClientRect();
    slider.style.left = (b.left - a.left) + 'px';
    slider.style.width = b.width + 'px';
    if (!animate) { void slider.offsetWidth; slider.style.transition = ''; }
  }

  place(active(), false);
  if (!sw._resizeBound) {
    window.addEventListener('resize', () => place(active(), false));
    sw._resizeBound = true;
  }

  buttons.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      if (btn.classList.contains('on')) return;
      buttons.forEach(b => b.classList.remove('on'));
      btn.classList.add('on');
      place(btn, true);            // slide the pill first…
      setTimeout(() => switchLanguage(btn.dataset.lang), 240);  // …then swap
    });
  });
}

function switchLanguage(code) {
  // Django reads the language from this cookie (cookie-based i18n).
  document.cookie = 'django_language=' + code + '; path=/; max-age=31536000; samesite=lax';

  const page = document.getElementById('page');
  fetch(window.location.href, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
    .then(r => r.text())
    .then(html => {
      const doc = new DOMParser().parseFromString(html, 'text/html');
      const fresh = doc.getElementById('page');
      if (!fresh || !page) { window.location.reload(); return; }
      page.style.opacity = '0';
      setTimeout(() => {
        page.innerHTML = fresh.innerHTML;
        document.documentElement.setAttribute('lang', doc.documentElement.getAttribute('lang') || code);
        initPage();                // re-bind everything on the swapped content
        page.style.opacity = '1';  // scroll position is preserved (same layout)
      }, 180);
    })
    .catch(() => window.location.reload());
}

/* Demo banner — dismiss + remember (lives outside #page, init once). */
(function () {
  const b = document.getElementById('demo-banner');
  if (!b) return;
  if (localStorage.getItem('demoDismissed') === '1') { b.style.display = 'none'; }
  const x = document.getElementById('demo-banner-x');
  if (x) x.addEventListener('click', () => {
    b.style.display = 'none';
    localStorage.setItem('demoDismissed', '1');
  });
})();

function initPage() {
  initIcons();
  initReveal();
  initFaq();
  initLangSwitch();
}

initPage();

// Safety: reveal anything above the fold that the observer didn't catch.
window.addEventListener('load', () => {
  setTimeout(() => {
    document.querySelectorAll('.reveal:not(.show)').forEach(el => {
      const r = el.getBoundingClientRect();
      if (r.top < window.innerHeight) el.classList.add('show');
    });
  }, 400);
});
