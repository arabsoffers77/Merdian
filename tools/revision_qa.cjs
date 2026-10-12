const {chromium}=require('C:/Users/ASUS/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('fs'),assert=require('assert/strict');
const out='_verify/media-update/revision';fs.mkdirSync(out,{recursive:true});
const media=JSON.parse(fs.readFileSync('assets/media/catalog.json','utf8'));
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe'});
 const results=[];
 for(const lang of ['en','ar']) for(const width of [1440,390]){
  const context=await browser.newContext({viewport:{width,height:900}});
  for(const name of (process.argv.includes('--projects-only')?['projects']:['index','about','services','projects','disciplines','contact'])){
   const page=await context.newPage(),errors=[],bad=[];
   page.on('pageerror',e=>errors.push(e.message));page.on('response',r=>{if(r.url().includes('127.0.0.1')&&r.status()>=400)bad.push(r.url());});
   const path=(lang==='en'?'en/':'')+name+'.html';
   await page.goto('http://127.0.0.1:4173/'+path,{waitUntil:'networkidle'});
   await page.waitForTimeout(1800);
   assert.equal(await page.locator('html').getAttribute('lang'),lang);
   if(lang==='ar')assert.equal(await page.locator('html').getAttribute('dir'),'rtl');
   if(lang==='ar'){
    await page.evaluate(()=>document.fonts.ready);
    assert(await page.evaluate(()=>Array.from(document.fonts).some(f=>f.family.includes('Noto Sans Arabic')&&f.status==='loaded')),'Noto Sans Arabic must load');
    assert((await page.locator('body').evaluate(e=>getComputedStyle(e).fontFamily)).includes('Noto Sans Arabic'));
   }
   const switchPath=lang==='ar'?'en/'+name+'.html':'../'+name+'.html';
   assert.equal(await page.locator('.language-switch').getAttribute('href'),switchPath);
   assert(await page.locator('.language-switch').isVisible());
   assert(!(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1)),path+' horizontal overflow '+width);
   if(width===390){await page.locator('.nav-toggle').click();assert(await page.locator('.main-nav').isVisible());await page.locator('.nav-toggle').click();await page.waitForTimeout(450);}
   await page.screenshot({path:`${out}/${lang}-${name}-${width}.png`});
   if(name==='index'){
    // Verify actual expansion across its original scroll interval.
    const metrics=await page.locator('.hero-media').evaluate(el=>({top:el.getBoundingClientRect().top+scrollY,vh:innerHeight}));
    await page.evaluate(m=>scrollTo(0,Math.max(0,m.top-m.vh*.92)),metrics);await page.waitForTimeout(550);
    const small=(await page.locator('.hero-media').boundingBox()).width;
    await page.evaluate(m=>scrollTo(0,m.top-m.vh*.16),metrics);await page.waitForTimeout(850);
    const large=(await page.locator('.hero-media').boundingBox()).width;
    assert(large>small+width*.12,'Hero film must expand on scroll');
    // Check all eight services retain their original perspective entrance.
    const folded=await page.locator('#services-grid .cell').evaluateAll(els=>els.map(e=>Number(gsap.getProperty(e,'rotationX'))));
    assert.equal(folded.length,8);assert(folded.every(x=>x<-13),'Services must start folded in 3D');
    await page.locator('#services-grid').scrollIntoViewIfNeeded();await page.waitForTimeout(2400);
    const arrived=await page.locator('#services-grid .cell').evaluateAll(els=>els.map(e=>({opacity:getComputedStyle(e).opacity,rx:Number(gsap.getProperty(e,'rotationX'))})));
    assert(arrived.every(x=>x.opacity==='1'&&Math.abs(x.rx)<.01),'All eight services must finish their entrance');
    await page.locator('#services-grid').screenshot({path:`${out}/${lang}-services-motion-${width}.png`});
    const head=page.locator('.feat-grid').locator('..').locator('h2');
    assert(await head.locator('.split-word').count()>0,'Selected work must retain word animation');
    const motion=await page.evaluate(()=>ScrollTrigger.getAll().some(t=>t.trigger&&t.trigger.matches('.hero-media')));
    assert(motion);results.push({lang,width,motion:{heroWidthBefore:small,heroWidthAfter:large,services:arrived}});
   }
   const images=page.locator('img:not(#pm-img):not(.drift-tile > img)');
   for(let i=0;i<await images.count();i++){
    const im=images.nth(i);if(!await im.isVisible())continue;await im.scrollIntoViewIfNeeded();
    await im.evaluate(el=>el.complete?null:new Promise(resolve=>{el.onload=resolve;el.onerror=resolve;setTimeout(resolve,4000)}));
    assert(await im.evaluate(el=>el.naturalWidth>0),`${path} broken image ${await im.getAttribute('src')}`);
   }
   if(name==='index'){
    const tiles=await page.locator('.drift-tile img').evaluateAll(els=>els.map(e=>e.src));
    assert(tiles.length<=30&&tiles.length>0);assert.equal(new Set(tiles).size,tiles.length);
    await page.locator('#about-drift-section').scrollIntoViewIfNeeded();await page.waitForTimeout(300);
    await page.screenshot({path:`${out}/${lang}-drift-${width}.png`});
    const film=page.locator('#hero-film');await film.scrollIntoViewIfNeeded();
    await page.waitForFunction(()=>{const v=document.getElementById('hero-film');return v.readyState>=2&&!v.paused;});
    const video=await film.evaluate(v=>({w:v.videoWidth,h:v.videoHeight,d:v.duration,src:v.currentSrc,quality:v.getVideoPlaybackQuality?{total:v.getVideoPlaybackQuality().totalVideoFrames,dropped:v.getVideoPlaybackQuality().droppedVideoFrames}:null}));
    assert.equal(video.w,width>760?1920:1280);assert(Math.abs(video.d-media.video.duration_seconds)<.05);assert(video.src.includes('mrasi-alsaada-2-loop-'));
    assert(await film.evaluate(v=>v.loop));
    await film.evaluate(v=>{v.currentTime=v.duration-.15;});await page.waitForTimeout(650);
    assert(await film.evaluate(v=>!v.paused&&v.currentTime<1),'Film must cross the loop boundary without stopping');
    await page.locator('.video-toggle').click();assert(await film.evaluate(v=>v.paused));
    await page.locator('.video-toggle').click();await page.waitForTimeout(1000);assert(!await film.evaluate(v=>v.paused));
    await page.screenshot({path:`${out}/${lang}-film-${width}.png`});results.push({lang,width,video,uniqueDriftImages:tiles.length});
   }
   if(name==='projects'){
    assert.equal(await page.locator('.proj-card').count(),30);
    const card=page.locator('#proj-mrasi-alsaada-2');await card.scrollIntoViewIfNeeded();await page.waitForTimeout(400);
    await page.waitForTimeout(850);
    assert.equal(await card.evaluate(el=>getComputedStyle(el).opacity),'1','Project must not remain hidden by a stagger animation');
    const ratios=await card.locator('img').evaluate(im=>({display:im.getBoundingClientRect().width/im.getBoundingClientRect().height,source:im.naturalWidth/im.naturalHeight}));
    assert(Math.abs(ratios.display-ratios.source)<.01,'Portrait must not be cropped or letterboxed');
    await page.screenshot({path:`${out}/${lang}-portraits-${width}.png`});
    await page.locator('#proj-tilal-district').screenshot({path:`${out}/${lang}-tilal-${width}.png`});
    await page.locator('#proj-al-shorouq').screenshot({path:`${out}/${lang}-shorouq-${width}.png`});
    await page.locator('[data-filter="coastal"]').click();
    assert(await page.locator('.proj-card:visible').count()<30);
    await page.locator('[data-filter="*"]').click();
    await page.waitForTimeout(2300);
    const first=page.locator('.proj-card').first();await first.scrollIntoViewIfNeeded();
    if(width===1440){
     const box=await first.boundingBox();await page.mouse.move(box.x+box.width*.82,box.y+box.height*.2);await page.waitForTimeout(650);
     const depth=await first.evaluate(e=>({ry:Number(gsap.getProperty(e,'rotationY')),scale:Number(gsap.getProperty(e.querySelector('img'),'scaleX')),transform:getComputedStyle(e.querySelector('img')).transform}));
     assert(Math.abs(depth.ry)>.15&&Math.abs(depth.ry)<1.3&&depth.scale>1.02&&depth.scale<1.05&&depth.transform!=='none','Portfolio hover must remain present and gentle');
     results.push({lang,width,projectDepth:depth});await page.mouse.move(2,2);await page.waitForTimeout(600);
    }
    await page.locator('.proj-card').first().click();assert.equal(await page.locator('#project-modal').getAttribute('aria-hidden'),'false');
    const grade=await page.locator('#pm-img').evaluate(e=>getComputedStyle(e).filter);assert(grade.includes('sepia(0.28)'),'Full image must use the same warm grade');
    if(lang==='ar')assert(/[\u0600-\u06ff]/.test(await page.locator('#pm-name').innerText()));
    await page.keyboard.press('Escape');
   }
   assert.deepEqual(errors,[],path+' script errors');assert.deepEqual(bad,[],path+' missing files');
   results.push({path,width,images:await images.count(),errors,bad});await page.close();
  }
  if(lang==='ar'){
   const review=await context.newPage();await review.goto('http://127.0.0.1:4173/delivery/media-review.html',{waitUntil:'networkidle'});
   assert.equal(await review.locator('article').count(),30);
   const original=await review.locator('article img').first().evaluate(e=>getComputedStyle(e).filter);
   assert(original.includes('sepia(0.28)'));
   await review.locator('article').first().scrollIntoViewIfNeeded();await review.screenshot({path:`${out}/grade-after-${width}.png`});
   await review.locator('#grade-toggle').click();assert.equal(await review.locator('article img').first().evaluate(e=>getComputedStyle(e).filter),'none');
   await review.locator('article').first().scrollIntoViewIfNeeded();await review.screenshot({path:`${out}/grade-before-${width}.png`});
   await review.locator('#grade-toggle').click();assert.equal(await review.locator('article img').first().evaluate(e=>getComputedStyle(e).filter),original);
   assert(!await review.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),'Media review horizontal overflow');
   await review.close();
  }
  await context.close();
 }
 for(const option of ['reduce','saveData']){
  const context=await browser.newContext({viewport:{width:390,height:844},reducedMotion:option==='reduce'?'reduce':'no-preference'});
  if(option==='saveData')await context.addInitScript(()=>Object.defineProperty(navigator,'connection',{value:{saveData:true}}));
  const page=await context.newPage();const requests=[];page.on('request',r=>{if(r.url().endsWith('.mp4'))requests.push(r.url());});
  await page.goto('http://127.0.0.1:4173/index.html',{waitUntil:'networkidle'});await page.locator('#hero-film').scrollIntoViewIfNeeded();await page.waitForTimeout(500);assert.equal(requests.length,0);await context.close();
 }
 const context=await browser.newContext({viewport:{width:900,height:900}});
 for(const path of ['index.html','en/index.html','ar/index.html','ar/projects.html']){
  const page=await context.newPage();await page.goto('http://127.0.0.1:4173/'+path);await page.waitForTimeout(1800);
  assert(!await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),path+' tablet overflow');await page.close();
 }
 const nojs=await browser.newContext({javaScriptEnabled:false});
 const defaultPage=await nojs.newPage();await defaultPage.goto('http://127.0.0.1:4173/');
 assert.equal(await defaultPage.locator('html').getAttribute('lang'),'ar','Arabic is the server-served default without JavaScript');
 await nojs.close();
 await browser.close();fs.writeFileSync(`${out}/${process.argv.includes('--projects-only')?'project-fix-results':'results'}.json`,JSON.stringify(results,null,2));console.log('PASS: bilingual routes and requested regression checks.');
})().catch(e=>{console.error(e);process.exit(1)});
