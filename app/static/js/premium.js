(() => {
  const drawer = document.getElementById('bag-drawer');
  if (drawer && typeof drawer.showModal === 'function') {
    document.querySelectorAll('[data-open-bag]').forEach(link => link.addEventListener('click', e => {
      if (e.ctrlKey || e.metaKey || e.shiftKey || e.altKey) return;
      e.preventDefault(); if (!drawer.open) drawer.showModal();
    }));
    drawer.querySelector('[data-close-bag]').addEventListener('click', () => drawer.close());
    drawer.addEventListener('click', e => { if (e.target === drawer) { const r=drawer.getBoundingClientRect(); if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom) drawer.close(); } });
    const url = new URL(location.href);
    if (url.searchParams.get('bag') === 'open') { drawer.showModal(); url.searchParams.delete('bag'); history.replaceState(null,'',url); }
  }
  const form = document.querySelector('[data-booking]');
  if (!form || form.querySelector('.flash.error')) return; // all fields visible for server validation errors
  const panels = [...form.querySelectorAll('[data-book-step]')];
  const next = form.querySelector('[data-book-next]'), back = form.querySelector('[data-book-back]'), submit = form.querySelector('[data-book-submit]');
  const preview = form.querySelector('[data-book-preview]');
  let step=0;
  const update=()=>{
    panels.forEach((p,i)=>p.hidden=i!==step);
    form.querySelectorAll('[data-step-indicator]').forEach((el,i)=>{el.classList.toggle('current',i===step); if(i===step)el.setAttribute('aria-current','step'); else el.removeAttribute('aria-current');});
    next.hidden=step===panels.length-1; back.hidden=step===0; submit.hidden=step!==panels.length-1;
    if(step===2) preview.textContent=`${form.elements.party_size.value} guests · ${form.elements.when.value.replace('T',' at ') || 'Choose your time'}`;
  };
  const valid=()=>[...panels[step].querySelectorAll('input,select')].every(el=>el.reportValidity());
  next.addEventListener('click',()=>{if(valid()){step++;update();panels[step].querySelector('input,select')?.focus();}});
  back.addEventListener('click',()=>{step--;update();});
  form.addEventListener('submit',e=>{if(step<2){e.preventDefault();next.click();}else if(!valid())e.preventDefault();});
  update();
})();
