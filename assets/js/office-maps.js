/* Enhance the client's exact office links with a single, shared map. */
(function(){
 'use strict';
 var region=document.querySelector('.office-maps');if(!region)return;
 var links=Array.from(region.querySelectorAll('[data-office-map]')),frame=region.querySelector('iframe'),caption=region.querySelector('.office-map-caption'),open=region.querySelector('.office-map-open'),loading=region.querySelector('.office-map-loading'),ar=document.documentElement.lang==='ar';
 function busy(value){if(loading)loading.hidden=!value;frame.parentElement.setAttribute('aria-busy',String(value));}
 frame.addEventListener('load',function(){busy(false);});
 // Native lazy iframe loading can stall when the site is opened from disk.
 frame.loading='eager';busy(true);
 function activate(link){
  var url=new URL(link.dataset.embed);url.searchParams.set('hl',ar?'ar':'en');
  links.forEach(function(item){if(item===link)item.setAttribute('aria-current','true');else item.removeAttribute('aria-current');});
  var name=link.querySelector('strong').textContent,address=link.querySelector('span').textContent;
  if(frame.src!==url.href){busy(true);frame.src=url.href;}
  frame.title=(ar?'خريطة ':'Map of ')+name+' · '+address;
  caption.textContent=name+' · '+address;open.href=link.href;
  open.setAttribute('aria-label',(ar?'فتح في خرائط Google':'Open in Google Maps')+' · '+name);
  region.dataset.active=link.dataset.officeMap;
 }
 links.forEach(function(link,i){
  link.addEventListener('click',function(e){if(e.button!==0||e.ctrlKey||e.metaKey||e.shiftKey||e.altKey)return;e.preventDefault();activate(link);});
  link.addEventListener('keydown',function(e){
   var next=null;
   if(e.key==='ArrowRight'||e.key==='ArrowLeft')next=(i+((e.key==='ArrowRight')!==ar?1:-1)+links.length)%links.length;
   else if(e.key==='Home')next=0;else if(e.key==='End')next=links.length-1;else if(e.key===' '){e.preventDefault();activate(link);return;}
   if(next!==null){e.preventDefault();activate(links[next]);links[next].focus({preventScroll:true});}
  });
 });
 activate(links.find(link=>link.getAttribute('aria-current')==='true')||links[0]);
})();
