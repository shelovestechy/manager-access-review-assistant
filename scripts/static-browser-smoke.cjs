const {chromium}=require('playwright');
const {pathToFileURL}=require('node:url');
const {resolve}=require('node:path');
const assert=require('node:assert/strict');
(async()=>{
 const browser=await chromium.launch({headless:true});
 try {
  const page=await browser.newPage({viewport:{width:390,height:844}});
  const errors=[];let outbound=0;
  page.on('pageerror',e=>errors.push(e.message));
  page.on('request',r=>{if(/^https?:/.test(r.url()))outbound++;});
  await page.goto(pathToFileURL(resolve('demo/index.html')).href);
  await page.waitForFunction(()=>document.querySelector('#scenario-select').options.length===23);

  const typography = await page.evaluate(() => {
    return {fontFamily:getComputedStyle(document.body).fontFamily,
      bundledFaces:document.fonts.size,
      background:getComputedStyle(document.body).backgroundColor,
      heading:getComputedStyle(document.querySelector('h1')).fontWeight};
  });
  assert.match(typography.fontFamily,/Segoe UI Variable/);
  assert.deepEqual(
    {bundledFaces:typography.bundledFaces,background:typography.background,heading:typography.heading},
    {bundledFaces:0,background:'rgb(245, 245, 245)',heading:'600'}
  );
  await page.selectOption('#scenario-select','hansu-seasonal');
  await page.locator('#expiry-request').waitFor({state:'visible'});
  assert.match(await page.locator('#expiry-draft').textContent(),/Hansu Hanhi/);
  await page.click('#summary-button');
  await page.waitForFunction(()=>document.querySelector('#summary-result').textContent.includes('Rule-based briefing'));
  await page.selectOption('#scenario-select','hansu-wrong-manager');
  await page.locator('#message').waitFor({state:'visible'});
  assert.equal(await page.locator('#review').isVisible(),false);
  await page.selectOption('#scenario-select','taavi-new-starter');
  await page.locator('#review').waitFor({state:'visible'});
  await page.check('input[name="addition"]');await page.fill('#reason','New research role');
  await page.click('#draft-form button[type="submit"]');
  await page.locator('#draft-result').waitFor({state:'visible'});
  assert.match(await page.locator('#draft-text').textContent(),/Taavi Ankka/);
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
  assert.equal(outbound,0);assert.deepEqual(errors,[]);
  console.log('PASS: standalone file URL, no HTTP calls, selection, briefing, denial, draft, mobile width');
 } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
