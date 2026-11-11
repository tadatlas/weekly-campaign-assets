const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();
for (const w of [375, 660]) {
  const p=await b.newPage({viewport:{width:w,height:900},deviceScaleFactor:2});
  await p.goto('file://'+process.cwd()+'/OFI_NSW_07Nov2026.html');await p.waitForTimeout(1500);
  const r=await p.evaluate(()=>[...document.querySelectorAll('a.es-button')].map(a=>{
    const cs=getComputedStyle(a); const sp=a.closest('span.es-button-border');
    return {t:a.textContent.trim().slice(0,16), pad:cs.padding, fs:cs.fontSize,
            aw:Math.round(a.getBoundingClientRect().width), sw:sp?Math.round(sp.getBoundingClientRect().width):null};
  }));
  console.log('WIDTH',w);
  for (const x of r) console.log('  '+x.t.padEnd(16)+' pad='+x.pad.padEnd(14)+' fs='+x.fs+' a='+x.aw+' span='+x.sw);
}
await b.close();})();
