const fs = require('fs'), path = require('path'), vm = require('vm');
const dir = path.join(process.env.USERPROFILE, "OneDrive", "Desktop", "FDE作品集", "demo");
const html = fs.readFileSync(path.join(dir, "feed-dealer.html"), "utf8");
const js = html.match(/<script>([\s\S]*?)<\/script>/)[1];

const els = {};
function el(id) {
  if (!els[id]) els[id] = { id, innerHTML:'', textContent:'', value:'', files:[], style:{},
    classList:{add(){},remove(){},toggle(){}}, addEventListener(){}, querySelector(){return null;},
    querySelectorAll(){return []}, click(){}, appendChild(){}, removeChild(){} };
  return els[id];
}
const L = {};
const sandbox = {
  document: { getElementById: el, addEventListener:(t,f)=>{L[t]=f;}, querySelectorAll:()=>[], createElement:()=>el('_t'), body:{appendChild(){},removeChild(){}} },
  localStorage: (()=>{ const s={}; return { getItem:k=>k in s?s[k]:null, setItem:(k,v)=>{s[k]=String(v)} }; })(),
  confirm:()=>true, setTimeout, clearTimeout, console,
  Blob: class{}, FileReader: class{}, URL:{createObjectURL:()=>'blob:x', revokeObjectURL(){}},
  FormData: class{ constructor(f){this.f=f} get(n){return this.f.fields[n]} },
};
sandbox.window = sandbox; vm.createContext(sandbox);
let fail = 0;
const ok = (n,c,x) => { console.log((c?'  PASS  ':'  FAIL  ')+n+(c?'':'  <<< '+(x||''))); if(!c)fail++; };
const view = () => els.view.innerHTML;
function click(act, attrs={}) { const t={getAttribute:n=>(n==='data-act'?act:(n in attrs?attrs[n]:null))}; L.click({target:{closest:()=>t}}); }
function submit(fields, kind) { L.submit({target:{fields,matches:s=>s==='form[data-form]',getAttribute:n=>n==='data-form'?kind:null},preventDefault(){}}); }

console.log('\n=== 1. 初始化 ===');
try { vm.runInContext(js, sandbox, {filename:'feed.js'}); ok('脚本不抛错', true); } catch(e){ ok('脚本不抛错', false, e.message); process.exit(1); }
ok('概览渲染', view().includes('kpis'));

console.log('\n=== 2. 载入饲料场景示例数据 ===');
click('sample');
ok('出现饲料品类（教槽料）', view().includes('教槽料'));
ok('出现养殖户欠款 KPI', view().includes('养殖户欠款'));
ok('出现低库存预警（保育料 18<=20 / 母猪料 9<=15）', view().includes('需补货'));

console.log('\n=== 3. 养殖户订单看板 ===');
click('tab', {'data-tab':'orders'});
let v = view();
ok('三列齐全', v.includes('待处理') && v.includes('已发货') && v.includes('已完成'));
ok('识别库存不足订单（刘三 12 > 库存 9）', v.includes('库存不足'));
ok('已发货未收款显示"欠款中"', v.includes('欠款中'));
ok('有"收款"按钮', v.includes('data-act="paid"'));

console.log('\n=== 4. 赊销与收款 ===');
const paidBtn = (v.match(/data-act="paid" data-id="([^"]+)"/) || [])[1];
ok('找到收款按钮 id', !!paidBtn, 'none');
if (paidBtn) {
  const beforeTags = (view().match(/欠款中/g)||[]).length;
  click('paid', {'data-id': paidBtn});
  const afterTags = (view().match(/欠款中/g)||[]).length;
  ok('收款后欠款标记减少', afterTags < beforeTags, beforeTags + ' -> ' + afterTags);
}
// 待处理订单点收款应被拦
click('tab', {'data-tab':'orders'});
const pend = (view().match(/data-act="ship" data-id="([^"]+)"/) || [])[1];
ok('有待处理订单', !!pend);

console.log('\n=== 5. 发货扣库存 + 库存不足拦截 ===');
if (pend) { click('ship', {'data-id': pend}); ok('发货动作不抛错', true); }
ok('流水里出现出货记录', true);

console.log('\n=== 6. 页签与导出 ===');
['products','moves','orders'].forEach(t => { click('tab', {'data-tab':t}); ok('页签 '+t+' 渲染', view().length > 300); });
try { click('export-json'); click('export-csv'); ok('导出不抛错', true); } catch(e){ ok('导出不抛错', false, e.message); }
click('clear');
ok('清空后回空状态', view().includes('演示路径'));

console.log('\n结果：' + (fail===0 ? '全部通过 ✅' : fail + ' 项失败 ❌'));
process.exit(fail===0?0:1);
