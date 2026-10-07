// Run after installing Playwright and Chromium. No external application services.
const { chromium } = require('playwright');
const { spawn } = require('node:child_process');
const { readFileSync, mkdirSync } = require('node:fs');
const assert = require('node:assert/strict');
const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));
const server = spawn('python', ['-m', 'access_review.web', '--port', '8877'], {stdio: 'inherit'});
let browser;
(async () => {
  let ready = false;
  for (let i=0; i<100; i++) {
    try { ready = (await fetch('http://127.0.0.1:8877/api/health')).ok; } catch {}
    if (ready) break;
    await delay(50);
  }
  assert(ready, 'Demo server did not start');
  browser = await chromium.launch({headless:true});
  const page = await browser.newPage({viewport:{width:1280,height:900}});
  const errors=[];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto('http://127.0.0.1:8877');
  await page.waitForFunction(() => document.querySelector('#scenario-select').options.length === 23);
  const cases=JSON.parse(readFileSync('scenarios/cases.json','utf8')).cases;
  for (const item of cases) {
    const responsePromise=page.waitForResponse(r=>r.url().endsWith('/api/review'));
    await page.selectOption('#scenario-select',item.id);
    const response=await responsePromise;
    if (item.expected.outcome==='allow') {
      assert.equal(response.status(),200,item.id);
      await page.waitForFunction(name=>document.querySelector('#employee-name').textContent===name && !document.querySelector('#review').hidden,item.display_name);
      assert.equal(await page.inputValue('#manager-id'),item.manager);
    } else {
      assert.equal(response.status(),item.expected.outcome==='deny'?403:400,item.id);
      await page.locator('#message').waitFor({state:'visible'});
      assert.equal(await page.locator('#review').isVisible(),false);
    }
  }
  await page.selectOption('#scenario-select','hansu-seasonal');
  await page.locator('#expiry-request').waitFor({state:'visible'});
  assert.match(await page.locator('#expiry-draft').textContent(),/Hansu Hanhi/);
  await page.click('#summary-button');
  await page.waitForFunction(()=>document.querySelector('#summary-result').textContent.includes('Rule-based briefing'));
  await page.evaluate(() => { document.documentElement.style.scrollBehavior='auto'; window.scrollTo({top:0,behavior:'instant'}); });
  mkdirSync('browser-results',{recursive:true});
  await page.screenshot({path:'browser-results/desktop.png',fullPage:true});
  await page.setViewportSize({width:390,height:844});
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,'Mobile horizontal overflow');
  await page.screenshot({path:'browser-results/mobile.png',fullPage:true});
  // A delayed response for an old case must not replace the newly opened case.
  await page.route('**/api/review',async route=>{
    if(route.request().postDataJSON().scenario_id==='mikki-privileged') await delay(300);
    await route.continue();
  });
  await page.selectOption('#scenario-select','mikki-privileged');
  await page.selectOption('#scenario-select','taavi-new-starter');
  await page.waitForFunction(()=>document.querySelector('#employee-name').textContent==='Taavi Ankka');
  await delay(500);
  assert.equal(await page.locator('#employee-name').textContent(),'Taavi Ankka');
  await page.check('input[name="addition"]');
  await page.fill('#reason','Taavi starts research work.');
  await page.click('#draft-form button[type="submit"]');
  await page.locator('#draft-result').waitFor({state:'visible'});
  assert.match(await page.locator('#draft-text').textContent(),/Taavi Ankka/);
  assert.deepEqual(errors,[]);
  console.log('PASS: 22 cases, denied/error states, expiry draft, briefing, mobile width, stale response, request draft');
})().catch(error=>{console.error(error);process.exitCode=1;}).finally(async()=>{if(browser)await browser.close();server.kill();});
