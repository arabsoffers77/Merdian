/* Three continuous source shots, buffered before a short frame-safe dissolve. */
(function(){
  'use strict';
  var hero=document.querySelector('.hero-carousel');if(!hero)return;
  var playlist;try{playlist=JSON.parse(hero.dataset.playlist);}catch(error){return;}
  if(playlist.length!==3)return;
  var films=Array.from(hero.querySelectorAll('.hero-scene')),buttons=Array.from(hero.querySelectorAll('.hero-scene-link')),poster=hero.querySelector('.hero-poster');
  var automatic=!matchMedia('(prefers-reduced-motion: reduce)').matches&&!(navigator.connection||{}).saveData;
  var active=0,visible=false,suspended=false,transitioning=false,generation=0,pending=null,revealTimer=null;
  var failed=new Set(),mobile=innerWidth<=760;
  hero.classList.toggle('hero-static',!automatic);
  function allowed(){return automatic&&visible&&!suspended&&!document.hidden;}
  function sync(index){hero.dataset.activeScene=String(index);hero.style.setProperty('--hero-progress','0');buttons.forEach(function(b,i){b.setAttribute('aria-pressed',String(i===index));b.classList.toggle('is-active',i===index);});}
  function framePosition(index){return (mobile&&playlist[index].position_mobile)||playlist[index].position||'50% 55%';}
  function load(index){var film=films[index];film.style.objectPosition=framePosition(index);if(!film.hasAttribute('src')){film.muted=true;film.src=mobile?playlist[index].mobile:playlist[index].desktop;film.load();}return film;}
  function next(){for(var i=1;i<3;i++){var n=(active+i)%3;if(!failed.has(n))return n;}return active;}
  function preload(){if(allowed()){var n=next();if(n!==active)load(n);}}
  function clearPending(){
    if(!pending)return;
    clearTimeout(pending.timeout);clearTimeout(pending.fallback);
    pending.film.removeEventListener('playing',pending.onPlaying);
    if(pending.frame!=null)pending.film.cancelVideoFrameCallback(pending.frame);
    pending=null;
  }
  function advance(index){
    if(index!==active||!allowed())return;
    var film=films[index],end=Math.min(playlist[index].duration||8,isFinite(film.duration)?film.duration:8),boundary=Math.max(1,end-.85);
    hero.style.setProperty('--hero-progress',String(Math.min(1,film.currentTime/boundary)));
    if(film.currentTime>=boundary&&!transitioning){var n=next();if(n!==active)switchTo(n);}
  }
  function watch(index){
    var film=films[index];if(!film.requestVideoFrameCallback)return;
    if(film.__frame!=null)film.cancelVideoFrameCallback(film.__frame);
    function frame(){film.__frame=null;if(index!==active||!allowed())return;advance(index);film.__frame=film.requestVideoFrameCallback(frame);}
    film.__frame=film.requestVideoFrameCallback(frame);
  }
  function runCurrent(){if(allowed()&&!failed.has(active))load(active).play().catch(function(){});}
  function switchTo(index){
    if(index===active||transitioning||failed.has(index))return;
    if(!automatic){active=index;poster.src=mobile?playlist[index].poster_mobile:playlist[index].poster;poster.removeAttribute('srcset');poster.alt=playlist[index].alt;poster.style.objectPosition=framePosition(index);sync(index);return;}
    if(!allowed())return;
    transitioning=true;var token=++generation,incoming=load(index),outgoing=films[active],shown=false;
    incoming.currentTime=0;
    function abort(){
      if(token!==generation)return;
      clearPending();incoming.pause();transitioning=false;failed.add(index);
      var n=next();if(allowed()&&n!==active)switchTo(n);
    }
    function show(){
      if(shown||token!==generation)return;
      if(!allowed()){clearPending();incoming.pause();transitioning=false;return;}
      if(incoming.readyState<2||incoming.paused)return;
      shown=true;clearPending();
      incoming.classList.add('is-current','is-playing');outgoing.classList.add('is-outgoing');
      var old=active;active=index;sync(index);watch(index);
      revealTimer=setTimeout(function(){films[old].pause();films[old].classList.remove('is-current','is-playing','is-outgoing');incoming.classList.remove('is-outgoing');transitioning=false;revealTimer=null;preload();},650);
    }
    function onPlaying(){
      if(token!==generation)return;
      // Some browsers throttle video-frame callbacks while opacity is zero.
      // 'playing' plus HAVE_CURRENT_DATA also guarantees a decoded first frame.
      if(incoming.requestVideoFrameCallback)pending.frame=incoming.requestVideoFrameCallback(show);
      pending.fallback=setTimeout(show,100);
    }
    pending={film:incoming,onPlaying:onPlaying,timeout:setTimeout(abort,8000),frame:null,fallback:null};
    incoming.addEventListener('playing',onPlaying,{once:true});incoming.play().catch(abort);
  }
  films.forEach(function(film,index){
    film.addEventListener('playing',function(){if(index===active){film.classList.add('is-current','is-playing');preload();watch(index);}});
    film.addEventListener('timeupdate',function(){advance(index);});
    film.addEventListener('ended',function(){if(index===active&&!transitioning&&allowed()){var n=next();if(n!==active)switchTo(n);}});
    film.addEventListener('error',function(){failed.add(index);if(index===active&&!transitioning){var n=next();if(n!==active)switchTo(n);}});
  });
  function stop(){
    generation++;clearPending();clearTimeout(revealTimer);revealTimer=null;transitioning=false;
    films.forEach(function(film,i){film.pause();if(film.__frame!=null){film.cancelVideoFrameCallback(film.__frame);film.__frame=null;}film.classList.toggle('is-current',i===active);film.classList.remove('is-outgoing');});
  }
  hero.heroPlayback={suspend:function(){suspended=true;stop();},resume:function(){suspended=false;runCurrent();},select:switchTo};
  buttons.forEach(function(button,index){button.addEventListener('click',function(){switchTo(index);});});
  hero.addEventListener('keydown',function(event){if(!['ArrowLeft','ArrowRight'].includes(event.key))return;event.preventDefault();var direction=(event.key==='ArrowRight')!==(document.documentElement.dir==='rtl')?1:2;var n=(active+direction)%3;switchTo(n);buttons[n].focus();});
  if('IntersectionObserver' in window)new IntersectionObserver(function(entries){visible=entries[0].isIntersecting;if(visible)runCurrent();else stop();},{threshold:.1}).observe(hero);
  else{visible=true;runCurrent();}
  document.addEventListener('visibilitychange',function(){if(document.hidden)stop();else runCurrent();});sync(0);
})();
