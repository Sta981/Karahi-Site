/* Keep scroll and expanded navigation groups across server-rendered page changes. */
(() => {
  const sidebar=document.querySelector('.sidebar, .rail');
  if(!sidebar) return;
  const nav=sidebar.querySelector('nav');
  if(!nav) return;
  const key='restroiq:sidebar:v3:'+ (sidebar.dataset.scope || sidebar.className);
  const groups=[...nav.querySelectorAll('details')];
  const groupKey=(g)=>g.querySelector('summary')?.textContent.trim().replace(/\s+/g,' ');
  let saved={};
  try {saved=JSON.parse(sessionStorage.getItem(key)||'{}');} catch (_) {}
  groups.forEach(g=>{
    const name=groupKey(g);
    const active=g.querySelector('a.active, a.selected');
    if(active) g.open=true;
    else if(saved.groups && Object.hasOwn(saved.groups,name)) g.open=saved.groups[name];
  });
  nav.scrollTop=Number(saved.scroll)||0;
  let ready=false;
  requestAnimationFrame(()=>{nav.scrollTop=Number(saved.scroll)||0;ready=true;});
  const save=()=>{
    if(!ready) return;
    try{sessionStorage.setItem(key,JSON.stringify({scroll:nav.scrollTop,groups:Object.fromEntries(groups.map(g=>[groupKey(g),g.open]))}));}catch(_){}
  };
  nav.addEventListener('scroll',save,{passive:true});
  groups.forEach(g=>g.addEventListener('toggle',save));
  sidebar.addEventListener('click',e=>{if(e.target.closest('a')) save();});
  window.addEventListener('pagehide',save);
})();
