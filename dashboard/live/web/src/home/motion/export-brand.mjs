const {chromium} = await import(process.env.PLAYWRIGHT_MODULE || 'playwright');
import {readFile} from 'node:fs/promises';
const svg=await readFile('../../../public/brand/orca-mark.svg','utf8');
const browser=await chromium.launch({executablePath:process.env.HYPERFRAMES_BROWSER_PATH,headless:true,args:['--single-process','--disable-gpu-compositing']});
const page=await browser.newPage({viewport:{width:28,height:28},deviceScaleFactor:3});
await page.setContent(`<style>html,body{margin:0;width:28px;height:28px}svg{width:28px;height:28px;display:block}</style>${svg}`);await page.screenshot({path:'assets/brand-mark.png'});await browser.close();
