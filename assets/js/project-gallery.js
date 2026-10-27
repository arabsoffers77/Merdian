/* Cinematic project media: native dialog, real films, full-frame images and facts. */
(function(){
 'use strict';
 var dialog=document.getElementById('project-modal');if(!dialog)return;
 var ar=document.documentElement.lang==='ar',motion=matchMedia('(prefers-reduced-motion: reduce)');
 var copy=ar?{film:'فيديو المشروع',image:'صورة',of:'من',loading:'جارٍ التحميل…',copied:'نُسخ رابط المشروع',copyFailed:'تعذّر نسخ الرابط',show:'عرض',zoom:'تكبير الصورة',unzoom:'تصغير الصورة'}:{film:'Project film',image:'Image',of:'of',loading:'Loading…',copied:'Project link copied',copyFailed:'Could not copy the link',show:'View',zoom:'Zoom image',unzoom:'Fit image'};
 var stage=dialog.querySelector('.pmodal-media'),images=[document.getElementById('pm-img'),document.getElementById('pm-img-next')],video=document.getElementById('pm-video'),thumbs=dialog.querySelector('.gallery-thumbs');
 var title=document.getElementById('pm-name'),description=document.getElementById('pm-desc'),category=document.getElementById('pm-cat'),details=document.getElementById('pm-details'),info=document.getElementById('pm-info');
 var infoButton=dialog.querySelector('[data-gallery-info]'),zoomButton=dialog.querySelector('[data-gallery-zoom]'),count=dialog.querySelector('.gallery-count'),status=dialog.querySelector('.gallery-status'),error=dialog.querySelector('.gallery-error'),loading=dialog.querySelector('.gallery-loading'),toast=dialog.querySelector('.cinema-toast');
 var items=[],index=0,imageIndex=0,card=null,generation=0,overflow='',closing=false,ownedHistory=false,scale=1,pan={x:0,y:0},gesture=null,flight=null,loadingTimer=0,toastTimer=0,closeTimer=0,resumeVideo=false,openingHash='';
 function currentImage(){return images[imageIndex];}
 function visibleMedia(){return items[index]&&items[index].type==='video'?video:currentImage();}
 function setBusy(busy){clearTimeout(loadingTimer);loading.hidden=true;stage.setAttribute('aria-busy',String(busy));if(busy)loadingTimer=setTimeout(function(){loading.hidden=false;},350);}
 function fail(token){if(token!==generation||!dialog.open)return;setBusy(false);images.forEach(function(im){im.hidden=true;});video.hidden=true;error.hidden=false;}
 function resetZoom(){scale=1;pan={x:0,y:0};images.forEach(function(im){im.style.transform='';});dialog.classList.remove('is-zoomed','is-dragging');zoomButton.setAttribute('aria-pressed','false');zoomButton.setAttribute('aria-label',copy.zoom);}
 function renderZoom(){
  var im=currentImage(),r=stage.getBoundingClientRect(),fit=Math.min(r.width/im.naturalWidth,r.height/im.naturalHeight);
  var maxX=Math.max(0,(im.naturalWidth*fit*scale-r.width)/2),maxY=Math.max(0,(im.naturalHeight*fit*scale-r.height)/2);
  pan.x=Math.max(-maxX,Math.min(maxX,pan.x));pan.y=Math.max(-maxY,Math.min(maxY,pan.y));
  im.style.transform='translate3d('+pan.x+'px,'+pan.y+'px,0) scale('+scale+')';dialog.classList.toggle('is-zoomed',scale>1);
  zoomButton.setAttribute('aria-pressed',String(scale>1));zoomButton.setAttribute('aria-label',scale>1?copy.unzoom:copy.zoom);
 }
 function zoom(value){if(zoomButton.disabled||currentImage().hidden||!currentImage().naturalWidth)return;currentImage().getAnimations().forEach(function(a){a.cancel();});scale=Math.max(1,Math.min(3,value));if(scale===1)resetZoom();else renderZoom();}
 function toggleInfo(value){
  var media=visibleMedia(),before=stage.getBoundingClientRect(),open=typeof value==='boolean'?value:!dialog.classList.contains('is-info-open');resetZoom();
  dialog.classList.toggle('is-info-open',open);info.inert=!open;info.setAttribute('aria-hidden',String(!open));infoButton.setAttribute('aria-expanded',String(open));
  if(dialog.open&&media&&!media.hidden&&!motion.matches){
   var after=stage.getBoundingClientRect(),w=media.naturalWidth||media.videoWidth,h=media.naturalHeight||media.videoHeight;
   if(w&&h&&after.width){var ratio=Math.min(before.width/w,before.height/h)/Math.min(after.width/w,after.height/h),dx=before.left+before.width/2-after.left-after.width/2;media.getAnimations().forEach(function(a){a.cancel();});media.animate([{transform:'translateX('+dx+'px) scale('+ratio+')'},{transform:'none'}],{duration:420,easing:'cubic-bezier(.16,1,.3,1)'});}
  }
  if(open)info.querySelector('[data-gallery-info-close]').focus({preventScroll:true});
 }
 function pauseAndClear(){video.pause();video.preload='none';video.removeAttribute('src');video.load();}
 function animateMedia(el,direction){if(motion.matches||!el.animate)return;el.animate([{opacity:.25,transform:'translateX('+(direction*18)+'px) scale(1.012)',clipPath:'inset(0 2% 0 2%)'},{opacity:1,transform:'none',clipPath:'inset(0 0 0 0)'}],{duration:420,easing:'cubic-bezier(.16,1,.3,1)'});}
 function sync(){
  var item=items[index],label=item.type==='video'?copy.film:(item.alt&&item.alt!=='Project image'&&item.alt!=='صورة من المشروع'&&item.alt.indexOf(ar?'فيديو':'film')!==-1?item.alt:copy.image+' '+(index+1));
  count.textContent=String(index+1).padStart(2,'0')+' / '+String(items.length).padStart(2,'0');status.textContent=label;
  Array.from(thumbs.children).forEach(function(button,i){button.setAttribute('aria-selected',String(i===index));button.tabIndex=i===index?0:-1;});
  var selected=thumbs.children[index];if(selected){stage.setAttribute('aria-labelledby',selected.id);selected.scrollIntoView({block:'nearest',inline:'nearest',behavior:motion.matches?'instant':'smooth'});}
  zoomButton.disabled=item.type==='video';
 }
 function show(next,animate){
  if(!items.length)return;var previous=index;index=(next+items.length)%items.length;var token=++generation,item=items[index],direction=(index>=previous?1:-1)*(ar?-1:1);
  resetZoom();pauseAndClear();error.hidden=true;setBusy(true);sync();
  if(item.type==='video'){
   images.forEach(function(im){im.hidden=true;});video.hidden=false;video.preload='metadata';video.poster=item.poster||'';video.muted=true;video.setAttribute('aria-label',title.textContent+' · '+copy.film);
   video.onloadedmetadata=function(){if(token===generation)setBusy(false);};
   video.onloadeddata=function(){if(token!==generation)return;setBusy(false);};video.onerror=function(){if(video.hasAttribute('src'))fail(token);};
   video.src=innerWidth<=760&&item.mobile?item.mobile:item.src;
   if(animate)animateMedia(video,direction);
   if(!motion.matches&&!(navigator.connection||{}).saveData)video.play().catch(function(){setBusy(false);});
  }else{
   var incoming=images[1-imageIndex],outgoing=currentImage(),loaded=false;incoming.hidden=true;incoming.style.transform='';
   incoming.onload=function(){
    if(loaded||token!==generation||!dialog.open)return;loaded=true;video.hidden=true;outgoing.hidden=true;incoming.hidden=false;imageIndex=1-imageIndex;setBusy(false);
    if(animate)animateMedia(incoming,direction);
    var neighbour=items[(index+1)%items.length];if(neighbour&&neighbour.type!=='video'){var preload=new Image();preload.src=innerWidth<=760&&neighbour.mobile?neighbour.mobile:neighbour.src;}
   };
   incoming.onerror=function(){fail(token);};incoming.alt=item.alt||title.textContent;incoming.src=innerWidth<=760&&item.mobile?item.mobile:item.src;
   if(incoming.complete&&incoming.naturalWidth)incoming.onload();
  }
 }
 function buildThumbs(){
  thumbs.replaceChildren();items.forEach(function(item,i){
   var button=document.createElement('button'),img=document.createElement('img');button.type='button';button.className='gallery-thumb';button.id='pm-thumb-'+i;button.setAttribute('role','tab');button.setAttribute('aria-controls','pm-stage');button.setAttribute('aria-label',copy.show+' '+(item.type==='video'?copy.film:copy.image+' '+(i+1)));
   img.src=item.thumb||item.poster||item.mobile||item.src;img.alt='';img.loading='lazy';img.decoding='async';button.appendChild(img);
   if(item.type==='video'){var icon=document.createElementNS('http://www.w3.org/2000/svg','svg');icon.setAttribute('viewBox','0 0 24 24');icon.setAttribute('fill','currentColor');icon.setAttribute('aria-hidden','true');var shape=document.createElementNS('http://www.w3.org/2000/svg','path');shape.setAttribute('d','m9 5 11 7-11 7Z');icon.appendChild(shape);button.appendChild(icon);}
   button.addEventListener('click',function(){show(i,true);});
   button.addEventListener('keydown',function(e){var n=null;if(e.key==='Home')n=0;else if(e.key==='End')n=items.length-1;if(n!==null){e.preventDefault();show(n,true);thumbs.children[index].focus({preventScroll:true});}});
   thumbs.appendChild(button);
  });
 }
 function projectHash(key){return '#project='+encodeURIComponent(key);}
 function keyFromHash(){var match=/^#project=([^&]+)/.exec(location.hash);if(!match)return null;try{return decodeURIComponent(match[1]);}catch(e){return null;}}
 function openProject(target,fromHistory){
  if(closing||!target)return;
  if(dialog.open){close('navigation',true);}
  card=target;var key=card.id.replace(/^proj-/,'');openingHash=fromHistory?'':location.hash;
  try{items=JSON.parse(card.getAttribute('data-gallery')||'[]');}catch(e){items=[];}
  if(!items.length)return;
  document.dispatchEvent(new Event('project:modalopen'));title.textContent=card.dataset.name||'';description.textContent=card.dataset.desc||'';category.textContent=card.dataset.catLabel||'';details.replaceChildren();
  try{JSON.parse(card.dataset.projectDetails||'[]').forEach(function(field){var group=document.createElement('div'),label=document.createElement('dt'),value=document.createElement('dd');label.textContent=field.label;value.textContent=field.value;group.append(label,value);details.appendChild(group);});}catch(e){}
  overflow=document.body.style.overflow;dialog.classList.remove('is-closing');toggleInfo(false);buildThumbs();dialog.setAttribute('aria-hidden','false');dialog.showModal();document.body.style.overflow='hidden';
  var hero=document.querySelector('.hero-video');if(hero&&hero.heroPlayback)hero.heroPlayback.suspend();
  ownedHistory=!fromHistory;if(!fromHistory)history.pushState({meridianProject:key},'',projectHash(key));
  show(0,false);dialog.querySelector('[data-pmodal-close]').focus({preventScroll:true});
  var source=card.querySelector('.proj-media img'),start=source.getBoundingClientRect(),end=stage.getBoundingClientRect();
  if(!motion.matches&&source.complete&&source.naturalWidth&&start.bottom>0&&start.top<innerHeight&&source.animate){
   var fit=Math.min(end.width/source.naturalWidth,end.height/source.naturalHeight),width=source.naturalWidth*fit,height=source.naturalHeight*fit;
   flight=source.cloneNode();flight.removeAttribute('srcset');flight.src=source.currentSrc||source.src;flight.className='cinema-flight';flight.alt='';flight.style.objectPosition=getComputedStyle(source).objectPosition;dialog.appendChild(flight);
   var clone=flight;
   clone.animate([{left:start.left+'px',top:start.top+'px',width:start.width+'px',height:start.height+'px'},{left:(end.left+(end.width-width)/2)+'px',top:(end.top+(end.height-height)/2)+'px',width:width+'px',height:height+'px'}],{duration:520,easing:'cubic-bezier(.16,1,.3,1)',fill:'forwards'}).finished.catch(function(){}).then(function(){clone.remove();if(flight===clone)flight=null;});
  }
 }
 function close(reason,immediate){
  if(!dialog.open||closing)return;closing=true;generation++;setBusy(false);pauseAndClear();if(flight){flight.remove();flight=null;}
  if(ownedHistory&&reason!=='navigation'&&location.hash===projectHash(card.id.replace(/^proj-/,'')))history.back();
  else if(reason!=='navigation'&&keyFromHash())history.replaceState(history.state,'',location.pathname+location.search+openingHash);
  ownedHistory=false;
  function finish(){dialog.close();dialog.setAttribute('aria-hidden','true');dialog.classList.remove('is-closing');toggleInfo(false);document.body.style.overflow=overflow;closing=false;var hero=document.querySelector('.hero-video');if(hero&&hero.heroPlayback)hero.heroPlayback.resume();if(card&&reason!=='navigation')card.focus({preventScroll:true});}
  if(immediate||motion.matches)finish();else{dialog.classList.add('is-closing');closeTimer=setTimeout(finish,200);}
 }
 function navigateHash(){var key=keyFromHash(),target=key&&document.getElementById('proj-'+key);if(target&&(!dialog.open||card!==target))openProject(target,true);else if(!target&&dialog.open)close('navigation');}
 document.querySelectorAll('.proj-card').forEach(function(c){c.addEventListener('click',function(e){e.preventDefault();openProject(c,false);});});
 dialog.querySelector('[data-pmodal-close]').addEventListener('click',function(){close('button');});dialog.addEventListener('cancel',function(e){e.preventDefault();close('escape');});
 dialog.querySelector('.gallery-prev').addEventListener('click',function(){show(index-1,true);});dialog.querySelector('.gallery-next').addEventListener('click',function(){show(index+1,true);});
 infoButton.addEventListener('click',function(){toggleInfo();});info.querySelector('[data-gallery-info-close]').addEventListener('click',function(){toggleInfo(false);infoButton.focus({preventScroll:true});});
 zoomButton.addEventListener('click',function(){zoom(scale>1?1:2);});dialog.querySelector('.gallery-retry').addEventListener('click',function(){show(index,false);});
 stage.addEventListener('dblclick',function(e){if(e.target.tagName==='IMG')zoom(scale>1?1:2);});
 stage.addEventListener('pointerdown',function(e){if(e.target.closest('button,video')||items[index]?.type==='video')return;gesture={x:e.clientX,y:e.clientY,px:pan.x,py:pan.y,pointer:e.pointerId};if(scale>1){stage.setPointerCapture(e.pointerId);dialog.classList.add('is-dragging');}});
 stage.addEventListener('pointermove',function(e){if(!gesture||scale===1)return;pan.x=gesture.px+e.clientX-gesture.x;pan.y=gesture.py+e.clientY-gesture.y;renderZoom();});
 stage.addEventListener('pointerup',function(e){if(!gesture)return;var dx=e.clientX-gesture.x,dy=e.clientY-gesture.y;dialog.classList.remove('is-dragging');if(scale===1&&Math.abs(dx)>55&&Math.abs(dx)>Math.abs(dy)*1.5)show(index+(dx<0?(ar?-1:1):(ar?1:-1)),true);gesture=null;});
 stage.addEventListener('pointercancel',function(){gesture=null;dialog.classList.remove('is-dragging');});
 dialog.addEventListener('keydown',function(e){
  if(e.target.tagName==='VIDEO'||e.ctrlKey||e.metaKey||e.altKey)return;
  if((e.key==='ArrowRight'||e.key==='ArrowLeft')&&!dialog.classList.contains('is-info-open')){e.preventDefault();show(index+((e.key==='ArrowRight')!==ar?1:-1),true);if(e.target.closest('.gallery-thumbs'))thumbs.children[index].focus({preventScroll:true});}
  if(e.key==='+'||e.key==='='){e.preventDefault();zoom(scale+.5);}if(e.key==='-'){e.preventDefault();zoom(scale-.5);}
 });
 dialog.querySelector('[data-gallery-share]').addEventListener('click',async function(){
  var url=new URL(location.href);url.hash=projectHash(card.id.replace(/^proj-/,''));var ok=false;
  try{await navigator.clipboard.writeText(url.href);ok=true;}catch(e){var field=document.createElement('textarea');field.value=url.href;field.style.cssText='position:fixed;opacity:0';dialog.appendChild(field);field.select();try{ok=document.execCommand('copy');}catch(ignore){}field.remove();}
  toast.textContent=ok?copy.copied:copy.copyFailed;toast.hidden=false;clearTimeout(toastTimer);toastTimer=setTimeout(function(){toast.hidden=true;},2400);
 });
 document.addEventListener('visibilitychange',function(){if(!dialog.open)return;if(document.hidden){resumeVideo=!video.paused;video.pause();}else if(resumeVideo&&!video.hidden)video.play().catch(function(){});});
 window.addEventListener('resize',resetZoom,{passive:true});window.addEventListener('popstate',navigateHash);window.addEventListener('hashchange',navigateHash);window.addEventListener('pagehide',function(){video.pause();});navigateHash();
})();
