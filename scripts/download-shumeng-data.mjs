// Uses a dedicated browser profile. The user signs in through the website;
// credentials and signed storage URLs are never logged or copied to manifests.
import { createRequire } from 'node:module';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { mkdir, writeFile } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { createHash } from 'node:crypto';
const root=join(dirname(fileURLToPath(import.meta.url)),'..');
const require=createRequire(join(root,'frontend/package.json'));
const { chromium }=require('@playwright/test');
const batch=process.argv[2] || '202609';
if(!/^\d{6}$/.test(batch))throw new Error('Expected YYYYMM batch');
const base='https://oj.shumeng.tech';
const edge='C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';
const context=await chromium.launchPersistentContext(join(root,'.runtime/shumeng-browser'),{
  executablePath:existsSync(edge)?edge:undefined,headless:false,viewport:{width:1200,height:850},
});
const page=context.pages()[0] || await context.newPage();
const target=join(root,'.runtime/external-data/shumeng',batch);
await mkdir(target,{recursive:true});
const manifest={batch,source:base,authorization:'User confirmed permission in CSP Lab conversation on 2026-10-10',
  officialHiddenData:false,origin:'Shumeng OJ independently recreated data; original large examples may also be included',problems:[]};
try {
  await page.goto(base+`/p/CSP${batch}A/files`,{waitUntil:'domcontentloaded'});
  const configAnchor=page.locator('.problem-files-testdata tr[data-filename="config.yaml"] a[href]').first();
  const configLink=await configAnchor.count()?await configAnchor.getAttribute('href'):null;
  const probeUrl=new URL(configLink || `/p/CSP${batch}A/file/config.yaml?type=testdata`,base).href;
  let probe=await context.request.get(probeUrl);
  let body=await probe.body();
  console.log(`Download access probe: HTTP ${probe.status()}, path ${new URL(probe.url()).pathname}, type ${probe.headers()['content-type'] || 'unknown'}`);
  if(!probe.ok() || /text\/html/i.test(probe.headers()['content-type'] || '')){
    await page.goto(base+`/login?redirect=${encodeURIComponent(`/p/CSP${batch}A/files`)}`,{waitUntil:'domcontentloaded'});
    if(process.env.SHUMENG_USERNAME && process.env.SHUMENG_PASSWORD){
      const user=page.locator('input[name="uname"]:visible').first();
      if(await user.count()){
        await user.fill(process.env.SHUMENG_USERNAME);
        await page.locator('input[name="password"]:visible').first().fill(process.env.SHUMENG_PASSWORD);
        await Promise.all([page.waitForURL(url=>!url.pathname.startsWith('/login'),{timeout:30000}),page.locator('input[name="password"]:visible').first().press('Enter')]);
      }
      delete process.env.SHUMENG_PASSWORD;
      probe=await context.request.get(probeUrl);
      body=await probe.body();
      if(probe.status()===403){
        await page.goto(probeUrl,{waitUntil:'domcontentloaded'});
        const message=await page.locator('body').innerText();
        console.log('Download response: '+message.replace(/\s+/g,' ').slice(0,1000));
        await writeFile(join(target,'access-status.json'),JSON.stringify({status:'DOWNLOAD_DENIED',httpStatus:403,batch,source:base,checkedAt:new Date().toISOString(),imported:false},null,2),'utf8');
        throw new Error('Authenticated testdata request is denied (HTTP 403). No formal data imported.');
      }
    }
    if(probe.ok() && !/text\/html/i.test(probe.headers()['content-type'] || '')){
      console.log('Authenticated testdata download is available.');
    } else {
    console.log('LOGIN REQUIRED: sign in in the opened website window. Do not send passwords in chat.');
    const end=Date.now()+30*60*1000;
    let lastStatus='';
    do {
      await page.waitForTimeout(15000);
      probe=await context.request.get(probeUrl);
      body=await probe.body();
      const status=`HTTP ${probe.status()}, path ${new URL(probe.url()).pathname}, type ${probe.headers()['content-type'] || 'unknown'}`;
      if(status!==lastStatus){console.log(`Download access: ${status}`);lastStatus=status;}
      if(probe.ok() && !/text\/html/i.test(probe.headers()['content-type'] || ''))break;
    } while(Date.now()<end);
    if(!probe.ok() || /text\/html/i.test(probe.headers()['content-type'] || ''))throw new Error('Login or testdata download permission is still required. No data imported.');
    }
  }
  for(const position of ['A','B','C','D','E']){
    const code=`CSP${batch}${position}`;
    await page.goto(base+`/p/${code}/files`,{waitUntil:'domcontentloaded'});
    const names=await page.locator('.problem-files-testdata tr[data-filename]').evaluateAll(rows=>rows.map(row=>({name:row.dataset.filename,size:Number(row.dataset.size),href:row.querySelector('a[href]')?.getAttribute('href')})));
    if(!names.length)throw new Error(`${code}: no visible testdata listing`);
    const folder=join(target,position);await mkdir(folder,{recursive:true});
    const problem={code,filesPage:base+`/p/${code}/files`,files:[]};
    for(const file of names){
      if(!/^(?:\d+\.(?:in|ans|out)|config\.yaml)$/.test(file.name))continue;
      if(file.size>64*1024*1024)throw new Error(`${code}: a file exceeds the 64 MiB import cap`);
      const response=await context.request.get(new URL(file.href || `/p/${code}/file/${encodeURIComponent(file.name)}?type=testdata`,base).href,{timeout:120000});
      if(!response.ok() || /text\/html/i.test(response.headers()['content-type'] || ''))throw new Error(`${code}: authenticated testdata download denied`);
      const data=await response.body();
      if(data.length!==file.size)throw new Error(`${code}: file size mismatch for ${file.name}`);
      await writeFile(join(folder,file.name),data);
      problem.files.push({name:file.name,bytes:data.length,sha256:createHash('sha256').update(data).digest('hex')});
      console.log(`${code}: ${file.name} verified (${data.length} bytes)`);
      await page.waitForTimeout(250);
    }
    if(!problem.files.some(f=>f.name==='config.yaml'))throw new Error(`${code}: missing scoring configuration`);
    manifest.problems.push(problem);
    await writeFile(join(target,'manifest.json'),JSON.stringify(manifest,null,2),'utf8');
  }
  console.log(`DOWNLOAD COMPLETE: ${manifest.problems.length} problems. Validation/import is a separate step.`);
} catch(error){
  // Playwright call logs may contain redirected signed URLs. Only the first
  // diagnostic line is safe to print; never print request headers or cookies.
  console.error(String(error.message).split('\n')[0].replace(/https?:\/\/\S+/g,'[URL omitted]'));
  process.exitCode=1;
}
finally{await context.close();}
