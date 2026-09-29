const {chromium}=require('playwright');
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),http=require('node:http');
const {pathToFileURL}=require('node:url');
const root=path.resolve(__dirname,'..');
const server=http.createServer((req,res)=>{
 const pathname=new URL(req.url,'http://localhost').pathname;
 if(!pathname.startsWith('/GamingCatalog/')){res.writeHead(404);return res.end();}
 const relative=decodeURIComponent(pathname.slice('/GamingCatalog/'.length))||'index.html';
 const file=path.resolve(root,relative);
 if(!file.startsWith(root+path.sep)){res.writeHead(403);return res.end();}
 fs.readFile(file,(err,data)=>{res.writeHead(err?404:200,{'Content-Type':file.endsWith('.js')?'text/javascript':file.endsWith('.json')?'application/json':file.endsWith('.css')?'text/css':'text/html'});res.end(err?'Not found':data)});
});
(async()=>{
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 const browser=await chromium.launch({headless:true,channel:'msedge'});
 try{
  for(const mode of ['file','http']){
   const base=mode==='file'?pathToFileURL(root+path.sep).href:`http://127.0.0.1:${server.address().port}/GamingCatalog/`;
   const page=await browser.newPage({viewport:{width:390,height:844}});const errors=[];
   await page.route('https://**/*',r=>r.abort());page.on('pageerror',e=>errors.push(e.message));
   await page.goto(base+'index.html');await page.waitForFunction(()=>document.querySelector('#total')?.textContent==='911');
   await page.evaluate(()=>localStorage.setItem('db-navigation-check','preserved'));
   assert.ok(await page.locator('.db-jump').isVisible());
   assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
   await page.click('.db-jump');assert.equal(page.url(),base+'db/index.html');
   await page.waitForFunction(()=>document.querySelectorAll('.game-item').length===50);
   assert.match(await page.locator('#searchInfo').textContent(),/17,065/);
   await page.locator('#searchInput').fill('Sonic');await page.locator('#searchInput').press('Enter');
   assert.equal(await page.locator('.game-item').count(),19);
   assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
   await page.getByRole('link',{name:'Jump to portal',exact:true}).click();assert.equal(page.url(),base+'index.html');
   await page.waitForFunction(()=>document.querySelector('#total')?.textContent==='911');
   assert.equal(await page.evaluate(()=>localStorage.getItem('db-navigation-check')),'preserved');
   await page.click('#language');await page.waitForFunction(()=>document.documentElement.lang==='en');
   assert.equal(await page.locator('.db-jump').textContent(),'Jump to DB');
   for(const filename of ['ps4-games-optimized.html','ps4-pwa-optimized.html','redirect.html','redirect-optimized.html']){
    await page.goto(base+'db/'+filename);assert.equal(await page.getByRole('link',{name:'Jump to portal',exact:true}).getAttribute('href'),'../index.html');
    assert.ok(await page.getByRole('link',{name:'Jump to portal',exact:true}).isVisible());
    if(filename.startsWith('ps4-'))await page.waitForFunction(()=>document.querySelectorAll('.game-item').length===50);
   }
   assert.deepEqual(errors,[]);await page.close();console.log('PASS: '+mode+' navigation, nested Pages path, bounded DB rendering/search, state retained, mobile, English, all DB return buttons');
  }
 }finally{await browser.close();server.close();}
})().catch(e=>{console.error(e);server.close();process.exitCode=1;});
