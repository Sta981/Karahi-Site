(() => {
  const header = document.querySelector('.premium-site .site-header');
  if (!header) return;
  const refresh = () => header.classList.toggle('is-scrolled', window.scrollY > 24);
  refresh(); window.addEventListener('scroll', refresh, {passive: true});
  const account = header.querySelector('.account-menu');
  if (account) {
    document.addEventListener('click', e => { if (!account.contains(e.target)) account.open = false; });
    document.addEventListener('keydown', e => { if (e.key === 'Escape' && account.open) { account.open = false; account.querySelector('summary').focus(); } });
  }
})();
