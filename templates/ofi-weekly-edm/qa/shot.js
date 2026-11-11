const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();
let p=await b.newPage({viewport:{width:660,height:900},deviceScaleFactor:2});
await p.goto('file://'+process.cwd()+'/OFI_NSW_07Nov2026.html');await p.waitForTimeout(2500);
await p.screenshot({path:'email_desk.png',fullPage:true});
p=await b.newPage({viewport:{width:375,height:812},deviceScaleFactor:2});
await p.goto('file://'+process.cwd()+'/OFI_NSW_07Nov2026.html');await p.waitForTimeout(2500);
await p.screenshot({path:'email_mob.png',fullPage:true});
await b.close();})();
