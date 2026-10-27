/* Pixel-row packing preserves the current cards, widths, effects and DOM order. */
(function(){
 'use strict';
 var grid=document.querySelector('.projects-grid');if(!grid)return;
 var cards=Array.from(grid.querySelectorAll('.proj-card')),raf=0,lastWidth=0;
 function arrange(){
  raf=0;var visible=cards.filter(function(c){return !c.hidden;}),wide=innerWidth>900,gap=parseFloat(getComputedStyle(grid).columnGap)||24;
  grid.classList.add('projects-masonry');
  cards.forEach(function(c){c.classList.remove('project-closing-card');});
  visible.forEach(function(c,i){var closing=wide&&visible.length%2===1&&i===visible.length-1;c.classList.toggle('project-closing-card',closing);c.style.setProperty('--project-columns',closing?12:[7,5,5,7][i%4]);});
  function measure(){visible.forEach(function(c){c.style.gridRowEnd='span '+Math.ceil(c.offsetHeight+gap);});return grid.offsetHeight;}
  measure();
  // Fit the penultimate card into the shorter lane before the full-width close.
  // Try both established widths and retain the compact packing, including after filters.
  if(wide&&visible.length>2&&visible.length%2===1){
   var tail=visible[visible.length-2],normal=[7,5,5,7][(visible.length-2)%4],heights={};
   [5,7].forEach(function(columns){tail.style.setProperty('--project-columns',columns);heights[columns]=measure();});
   var best=heights[5]===heights[7]?normal:(heights[5]<heights[7]?5:7);tail.style.setProperty('--project-columns',best);measure();
  }
  if(window.ScrollTrigger)window.ScrollTrigger.refresh();
 }
 function schedule(){if(!raf)raf=requestAnimationFrame(arrange);}
 var resize=new ResizeObserver(function(entries){var width=grid.clientWidth;if(width!==lastWidth){lastWidth=width;schedule();}else if(entries.some(function(e){return e.target!==grid;}))schedule();});
 resize.observe(grid);cards.forEach(function(c){resize.observe(c.querySelector('.proj-media'));resize.observe(c.querySelector('.proj-meta'));var img=c.querySelector('img');if(img)img.addEventListener('load',schedule);});
 document.addEventListener('project:filter',schedule);window.addEventListener('resize',schedule,{passive:true});
 if(document.fonts)document.fonts.ready.then(schedule);arrange();
})();
