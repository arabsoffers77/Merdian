// Local browser verification; does not connect to Drive or change the website.
const {chromium}=require('C:/Users/ASUS/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('fs');
const assert=require('assert/strict');
const out='_verify/media-update'; fs.mkdirSync(out,{recursive:true});
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe'});
 const results=[];
 for(const width of [1440,390]){
  const context=await browser.newContext({viewport:{width,height:900},deviceScaleFactor:1});
  for(const name of (process.argv.includes('--final')?['index','projects']:['index','about','services','projects','disciplines','contact'])){
   const page=await context.newPage(); const errors=[]; const failed=[];
   page.on('pageerror',e=>errors.push(e.message));
   page.on('response',r=>{if(r.url().startsWith('http://127.0.0.1')&&r.status()>=400)failed.push(r.url());});
   await page.goto(`http://127.0.0.1:4173/${name}.html`,{waitUntil:'networkidle'});
   await page.waitForTimeout(1700);
   const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1);
   assert(!overflow,`${name} ${width}: horizontal overflow`);
   // Visit each image to trigger native lazy loading and reveal animations.
   const images=page.locator('img:not(#pm-img):not(.drift-tile > img)');
   for(let i=0;i<await images.count();i++){
    const img=images.nth(i);
    if(!await img.isVisible())continue;
    await img.scrollIntoViewIfNeeded();
    await img.evaluate(el=>el.complete?null:new Promise(resolve=>{el.onload=resolve;el.onerror=resolve;setTimeout(resolve,5000)}));
    assert(await img.evaluate(el=>el.naturalWidth>0),`${name}: broken ${await img.getAttribute('src')}`);
   }
   if(name==='index'){
    const film=page.locator('#hero-film'); await film.scrollIntoViewIfNeeded();
    await page.waitForFunction(()=>{const v=document.getElementById('hero-film');return v.readyState>=2&&!v.paused;});
    const video=await film.evaluate(v=>({src:v.currentSrc,w:v.videoWidth,h:v.videoHeight,time:v.currentTime,muted:v.muted,duration:v.duration}));
    assert(video.src.includes(width<760?'mobile.mp4':'desktop.mp4'));
    const expected=JSON.parse(fs.readFileSync('assets/media/catalog.json','utf8')).video.duration_seconds;
    assert(video.muted&&Math.abs(video.duration-expected)<.05);
    await page.locator('.video-toggle').click(); assert(await film.evaluate(v=>v.paused));
    await page.locator('.video-toggle').click(); await page.waitForTimeout(250);assert(!await film.evaluate(v=>v.paused));
    const bounds=await page.locator('.hero-video').boundingBox();
    const control=await page.locator('.video-toggle').boundingBox();
    assert(control.y<bounds.y+bounds.height*.2,'Film control must stay clear of source watermark');
    await page.screenshot({path:`${out}/home-film-${width}.png`});
    results.push({width,video});
   }
   if(name==='projects'){
    assert.equal(await page.locator('.proj-card').count(),30);
    await page.locator('[data-filter="coastal"]').click();
    assert(await page.locator('.proj-card:not([hidden])').count()>0);
    assert(await page.locator('.proj-card:not([hidden])').count()<30);
    await page.locator('[data-filter="*"]').click();
    const card=page.locator('.proj-card').first();const source=await card.getAttribute('data-full-image');
    await card.click(); await page.waitForTimeout(200);
    assert.equal(await page.locator('#project-modal').getAttribute('aria-hidden'),'false');
    assert.equal(await page.locator('#pm-img').getAttribute('src'),source);
    await page.keyboard.press('Escape');
    assert.equal(await page.locator('#project-modal').getAttribute('aria-hidden'),'true');
   }
   await page.evaluate(()=>scrollTo(0,0)); await page.waitForTimeout(500);
   await page.screenshot({path:`${out}/${name}-${width}.png`});
   assert.deepEqual(errors,[],`${name} script errors`);assert.deepEqual(failed,[],`${name} missing resources`);
   results.push({page:name,width,images:await images.count(),overflow,errors,failed});
   await page.close();
  }
  await context.close();
 }
 const reduced=await browser.newContext({viewport:{width:390,height:844},reducedMotion:'reduce'});
 const page=await reduced.newPage();const videos=[];page.on('request',r=>{if(r.url().endsWith('.mp4'))videos.push(r.url());});
 await page.goto('http://127.0.0.1:4173/index.html',{waitUntil:'networkidle'});
 await page.locator('#hero-film').scrollIntoViewIfNeeded();await page.waitForTimeout(500);
 assert.equal(videos.length,0,'Reduced motion must not auto-download video');
 await page.locator('.video-toggle').click();await page.waitForFunction(()=>!document.getElementById('hero-film').paused);
 assert.equal(videos.length,1);results.push({reducedMotion:'No video until play requested'});
 const saving=await browser.newContext({viewport:{width:390,height:844}});
 await saving.addInitScript(()=>Object.defineProperty(navigator,'connection',{value:{saveData:true},configurable:true}));
 const savePage=await saving.newPage();const saveRequests=[];
 savePage.on('request',r=>{if(r.url().endsWith('.mp4'))saveRequests.push(r.url());});
 await savePage.goto('http://127.0.0.1:4173/index.html',{waitUntil:'networkidle'});
 await savePage.locator('#hero-film').scrollIntoViewIfNeeded();await savePage.waitForTimeout(400);
 assert.equal(saveRequests.length,0,'Data-saving mode must not auto-download video');
 results.push({saveData:'No automatic video transfer'});
 const review=await saving.newPage();await review.goto('http://127.0.0.1:4173/delivery/media-review.html');
 assert.equal(await review.locator('article').count(),30);
 await browser.close();fs.writeFileSync(`${out}/${process.argv.includes('--final')?'final-results':'results'}.json`,JSON.stringify(results,null,2));console.log('PASS: desktop/mobile images, video, filters, modal, reduced motion, data saving and media review.');
})().catch(e=>{console.error(e);process.exit(1)});
