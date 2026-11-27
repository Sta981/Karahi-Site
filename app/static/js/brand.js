(() => {
  document.querySelectorAll('[data-password]').forEach(button => button.addEventListener('click', () => {
    const field = document.getElementById(button.dataset.password);
    if (!field) return;
    const show = field.type === 'password'; field.type = show ? 'text' : 'password';
    button.textContent = show ? 'Hide' : 'Show'; button.setAttribute('aria-pressed', String(show));
  }));
  const department = document.getElementById('department');
  if (department) {
    const choices = [...document.querySelectorAll('[data-department]')];
    function sync() { choices.forEach(b => { const active = b.dataset.department === department.value; b.classList.toggle('selected',active); b.setAttribute('aria-pressed',String(active)); }); }
    choices.forEach(b => b.addEventListener('click', () => { department.value=b.dataset.department; sync(); department.focus(); }));
    department.addEventListener('change',sync); sync();
  }
  if ('IntersectionObserver' in window && !matchMedia('(prefers-reduced-motion: reduce)').matches) {
    const observer = new IntersectionObserver(entries => entries.forEach(e => { if(e.isIntersecting){e.target.classList.add('revealed');observer.unobserve(e.target);} }),{threshold:.08});
    document.documentElement.classList.add('motion-ready');
    document.querySelectorAll('[data-reveal]').forEach(el=>observer.observe(el));
  }
})();
