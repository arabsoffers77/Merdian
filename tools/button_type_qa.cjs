/* Regression: localized rolling labels must fit, center, and keep their size. */
const {chromium}=require('C:/Users/ASUS/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('fs'),assert=require('assert/strict');
const out='_verify/media-update/buttons';fs.mkdirSync(out,{recursive:true});
const pages=['index','about','services','projects','disciplines','contact'];

async function inspectButtons(page,state){
 return page.locator('.btn').evaluateAll((buttons,state)=>buttons.map(button=>{
  const label=button.querySelector(state==='rest'?'.st-row:not(.st-b)':'.st-b');
  const mask=button.querySelector('.slide-txt'),b=button.getBoundingClientRect();
  const s=getComputedStyle(button),problems=[];
  if(label){
   const range=document.createRange();range.selectNodeContents(label);
   const text=range.getBoundingClientRect(),m=mask.getBoundingClientRect(),r=label.getBoundingClientRect();
   if(text.width>m.width+1)problems.push('clipped label width');
   if(Math.abs((text.left+text.right-m.left-m.right)/2)>1.5)problems.push('label not centered');
   if(Math.abs(r.top-m.top)>1.5||Math.abs(r.bottom-m.bottom)>1.5)problems.push('label not in visible row');
   if(parseFloat(s.lineHeight)<parseFloat(s.fontSize)*(document.dir==='rtl'?1.79:1.49))problems.push('insufficient line height');
   if(r.height<parseFloat(s.lineHeight)+parseFloat(s.fontSize)*.23)problems.push('missing glyph breathing room');
   if(document.dir==='rtl'&&Number(new DOMMatrixReadOnly(getComputedStyle(button.querySelector('.arr')).transform).a)>=0)problems.push('RTL arrow lost its direction');
  }
  const walker=document.createTreeWalker(button,NodeFilter.SHOW_TEXT);
  while(walker.nextNode()){
   const node=walker.currentNode;
   if(!node.textContent.trim()||node.parentElement.closest('.st-row'))continue;
   const range=document.createRange();range.selectNodeContents(node);
   for(const r of range.getClientRects())if(r.left<b.left-1||r.right>b.right+1||r.top<b.top-1||r.bottom>b.bottom+1)problems.push('plain label outside button');
  }
  return {label:label?.textContent.trim()||button.textContent.trim(),width:button.offsetWidth,height:button.offsetHeight,problems};
 }),state);
}

(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe'});
 const results=[];
 try{
  for(const lang of ['ar','en'])for(const width of [1440,390,320]){
   const context=await browser.newContext({viewport:{width,height:900}});
   for(const name of pages){
    const page=await context.newPage(),errors=[],missing=[];
    page.on('pageerror',e=>errors.push(e.message));
    page.on('response',r=>{if(r.url().includes('127.0.0.1')&&r.status()>=400)missing.push(r.url());});
    const path=(lang==='en'?'en/':'')+name+'.html';
    await page.goto('http://127.0.0.1:4173/'+path,{waitUntil:'networkidle'});
    await page.evaluate(()=>document.fonts.ready);await page.waitForTimeout(1600);
    if(lang==='ar'){
     assert((await page.locator('body').evaluate(e=>getComputedStyle(e).fontFamily)).includes('Noto Sans Arabic'));
     assert(await page.evaluate(()=>Array.from(document.fonts).some(f=>f.family==='Noto Sans Arabic'&&f.status==='loaded')),'New Arabic font must actually load');
    }
    assert(!await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),path+' horizontal overflow '+width);
    const buttons=page.locator('.btn'),count=await buttons.count();
    for(let i=0;i<count;i++){
     const button=buttons.nth(i);await button.scrollIntoViewIfNeeded();await page.waitForTimeout(350);
     await page.mouse.move(0,0);await button.evaluate(e=>e.blur());await page.waitForTimeout(400);
     const rest=(await inspectButtons(page,'rest'))[i];assert.deepEqual(rest.problems,[],`${path} ${width} resting ${rest.label}`);
     if(await button.locator('.slide-txt').count()){
      await button.hover();await page.waitForTimeout(450);
      const hover=(await inspectButtons(page,'hover'))[i];assert.deepEqual(hover.problems,[],`${path} ${width} hover ${hover.label}`);
      assert.equal(hover.width,rest.width);assert.equal(hover.height,rest.height);
      if(name==='index'&&i<2&&width!==320)await button.screenshot({path:`${out}/${lang}-${width}-button-${i}-hover.png`});
      await page.mouse.move(0,0);await button.focus();await page.waitForTimeout(450);
      const focus=(await inspectButtons(page,'hover'))[i];assert.deepEqual(focus.problems,[],`${path} ${width} keyboard ${focus.label}`);
      await button.evaluate(e=>e.blur());await page.waitForTimeout(400);
     }
    }
    if(name==='index'){
     await page.evaluate(()=>scrollTo(0,0));await page.waitForTimeout(450);
     await page.screenshot({path:`${out}/${lang}-home-${width}.png`});
     await page.locator('.hero-ctas').screenshot({path:`${out}/${lang}-${width}-buttons-rest.png`});
     await page.locator('.hero-ctas .btn').first().hover();await page.waitForTimeout(450);
     await page.locator('.hero-ctas').screenshot({path:`${out}/${lang}-${width}-buttons-hover.png`});
    }
    assert.deepEqual(errors,[],path+' script errors');assert.deepEqual(missing,[],path+' missing assets');
    results.push({path,width,buttons:count,errors,missing});await page.close();
   }
   await context.close();
  }
  // Stress rolling labels at twice their normal text size.
  const page=await browser.newPage({viewport:{width:390,height:900}});
  await page.goto('http://127.0.0.1:4173/',{waitUntil:'networkidle'});await page.evaluate(()=>document.fonts.ready);
  await page.addStyleTag({content:'.btn{font-size:28px!important}'});await page.waitForTimeout(1600);
  const big=await inspectButtons(page,'rest');big.forEach(x=>assert.deepEqual(x.problems,[],x.label+' enlarged text'));
  assert(!await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),'Enlarged buttons must still fit');
  await page.screenshot({path:`${out}/ar-enlarged-buttons.png`});await page.close();
  fs.writeFileSync(`${out}/results.json`,JSON.stringify(results,null,2));
  console.log(`PASS: ${results.length} page/viewport checks; rolling labels at rest, hover, keyboard focus, and enlarged text.`);
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
