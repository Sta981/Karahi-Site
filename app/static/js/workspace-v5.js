(() => {
  document.querySelectorAll('[data-lines]').forEach(form => {
    const list=form.querySelector('[data-line-list]');
    const original=list.firstElementChild.cloneNode(true);
    const update=()=>{
      let total=0;const rows=[...list.querySelectorAll('[data-line]')];
      rows.forEach(row=>{
        const dish=row.querySelector('[name=item_id]');
        total+=dish ? Number(dish.selectedOptions[0]?.dataset.price||0)*Number(row.querySelector('[name=qty]').value||0) : Number(row.querySelector('[name=quantity]').value||0)*Number(row.querySelector('[name=cost]').value||0);
        row.querySelector('[data-remove]').disabled=rows.length===1;
      });
      form.querySelector('[data-total]').textContent=total.toFixed(2);
      form.querySelector('[data-add]').disabled=rows.length>=20;
    };
    form.addEventListener('click',e=>{
      if(e.target.closest('[data-add]') && list.children.length<20){const row=original.cloneNode(true);list.append(row);row.querySelector('select').focus();update();}
      if(e.target.closest('[data-remove]')&&list.children.length>1){e.target.closest('[data-line]').remove();update();}
    });
    form.addEventListener('input',update);form.addEventListener('change',update);update();
  });
  const board=document.querySelector('[data-kitchen-board]');
  if(board){
    const tick=()=>document.querySelectorAll('[data-elapsed]').forEach(el=>{const minutes=Math.max(0,Math.floor((Date.now()-Date.parse(el.dataset.elapsed))/60000));if(Number.isFinite(minutes)){el.textContent=minutes+' min';el.classList.toggle('late',minutes>=25);}});
    tick();setInterval(tick,1000);let submitting=false;board.addEventListener('submit',()=>{submitting=true;});
    setInterval(()=>{if(!submitting&&!document.hidden&&!document.fullscreenElement&&!document.activeElement?.closest('form'))location.reload();},30000);
    document.querySelector('[data-fullscreen]')?.addEventListener('click',()=>{if(document.fullscreenElement)document.exitFullscreen();else document.documentElement.requestFullscreen?.().catch(()=>{});});
  }
  document.querySelector('[data-print]')?.addEventListener('click',()=>window.print());
})();
