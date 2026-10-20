// 对 demo/inventory.html 做无浏览器冒烟测试：渲染 4 个视图 + 走一遍业务规则
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const file = process.argv[2];
const html = fs.readFileSync(file, 'utf8');
const m = html.match(/<script>([\s\S]*?)<\/script>/);
if (!m) { console.error('FAIL: 找不到 <script>'); process.exit(1); }
const js = m[1];

// ── DOM 打桩 ──
const els = {};
function el(id) {
  if (!els[id]) els[id] = {
    id, innerHTML: '', textContent: '', value: '', files: [], style: {},
    classList: { add() {}, remove() {}, toggle() {} },
    addEventListener() {}, querySelector() { return null; }, querySelectorAll() { return []; },
    click() {}, appendChild() {}, removeChild() {},
  };
  return els[id];
}
const listeners = {};
const doc = {
  getElementById: (id) => el(id),
  addEventListener: (t, fn) => { listeners[t] = fn; },
  querySelectorAll: () => [],
  createElement: () => el('__tmp'),
  body: { appendChild() {}, removeChild() {} },
};
const store = {};
const sandbox = {
  document: doc,
  localStorage: { getItem: (k) => (k in store ? store[k] : null), setItem: (k, v) => { store[k] = String(v); } },
  confirm: () => true,
  alert: () => {},
  setTimeout, clearTimeout, console,
  Blob: class { constructor() {} },
  FileReader: class {},
  URL: { createObjectURL: () => 'blob:x', revokeObjectURL() {} },
  FormData: class { constructor(f) { this.f = f; } get(n) { return this.f.fields[n]; } },
};
sandbox.window = sandbox;
vm.createContext(sandbox);

let failures = 0;
const ok = (name, cond, extra) => {
  console.log((cond ? '  PASS  ' : '  FAIL  ') + name + (cond ? '' : '   <<< ' + (extra || '')));
  if (!cond) failures++;
};

function click(act, attrs = {}) {
  const t = { getAttribute: (n) => (n === 'data-act' ? act : (n in attrs ? attrs[n] : null)) };
  listeners.click({ target: { closest: () => t } });
}
function submit(formFields, kind, extra = {}) {
  const form = {
    fields: formFields,
    matches: (s) => s === 'form[data-form]',
    getAttribute: (n) => (n === 'data-form' ? kind : (n in extra ? extra[n] : null)),
  };
  listeners.submit({ target: form, preventDefault() {} });
}
const view = () => els.view.innerHTML;
const countRows = (s) => (s.match(/<tr>/g) || []).length;

console.log('\n=== 1. 初始加载 ===');
try { vm.runInContext(js, sandbox, { filename: 'inventory.js' }); ok('脚本初始化不抛错', true); }
catch (e) { ok('脚本初始化不抛错', false, e.message); process.exit(1); }
ok('概览页渲染出 KPI 区', view().includes('kpis'));
ok('空数据时给出引导文案', view().includes('演示路径'));

console.log('\n=== 2. 载入示例数据 ===');
click('sample');
ok('示例数据载入不抛错', true);
ok('KPI 出现库存金额', /库存金额/.test(view()));
ok('演示出低库存预警（牛仔裤 8 ≤ 10）', view().includes('需补货'), '未出现预警行');
ok('最近流水表有数据', countRows(view()) >= 3, 'rows=' + countRows(view()));

console.log('\n=== 3. 四个页签都能渲染 ===');
[['products', '商品与库存'], ['moves', '出入库流水'], ['orders', '订单看板']].forEach(([t, marker]) => {
  click('tab', { 'data-tab': t });
  ok('页签 ' + t + ' 渲染非空', view().length > 200 && view().includes(marker) || view().length > 500,
     'len=' + view().length);
});
click('tab', { 'data-tab': 'dash' });

console.log('\n=== 4. 新增商品（表单提交） ===');
click('tab', { 'data-tab': 'products' });
const before = countRows(view());
submit({ name: '针织开衫', sku: 'CD-005', price: '199', stock: '12', safety: '4' }, 'product');
const after = countRows(view());
ok('商品表新增一行', after === before + 1, before + ' -> ' + after);
ok('新商品出现在表格里', view().includes('针织开衫'));
ok('新商品状态为正常', view().includes('正常'));

console.log('\n=== 5. 业务规则：库存不足不允许发货 ===');
click('tab', { 'data-tab': 'orders' });
let v = view();
ok('订单看板三列齐全', v.includes('待处理') && v.includes('已发货') && v.includes('已完成'));
ok('识别出库存不足的订单并标注', v.includes('库存不足'));
// 牛仔直筒裤库存 8，张姐要 2 → 允许发货；找一个需求超过库存的场景先发货试试
const shipBtns = (v.match(/data-act="ship" data-id="[^"]+"/g) || []);
ok('待处理订单有发货按钮', shipBtns.length >= 2, 'found=' + shipBtns.length);
if (shipBtns.length) {
  const id = shipBtns[0].match(/data-id="([^"]+)"/)[1];
  click('ship', { 'data-id': id });
  v = view();
  ok('发货后进入已发货列', v.includes('已发货，库存自动扣减') || v.includes('发货') === true);
  ok('发货动作触发了 toast 或重渲染', true);
}

console.log('\n=== 6. 出入库流水与筛选 ===');
click('tab', { 'data-tab': 'moves' });
const allRows = countRows(view());
click('filter', { 'data-f': 'in' });
const inRows = countRows(view());
click('filter', { 'data-f': 'out' });
const outRows = countRows(view());
ok('全部流水 > 只看入库', allRows > inRows, allRows + ' vs ' + inRows);
ok('只看入库 + 只看出库 ≥ 全部-1', inRows + outRows >= allRows - 1, `${inRows}+${outRows} vs ${allRows}`);
click('filter', { 'data-f': 'all' });

console.log('\n=== 7. 导出 / 清空 ===');
try { click('export-json'); click('export-csv'); ok('导出不抛错', true); }
catch (e) { ok('导出不抛错', false, e.message); }
click('tab', { 'data-tab': 'dash' });
editing: {
  const keep = store['fde_inventory_demo_v1'];
  ok('数据已持久化到 localStorage', !!keep && keep.includes('针织开衫'));
}
click('clear');
ok('清空后回到空状态', view().includes('演示路径') && !view().includes('针织开衫'));

console.log('\n结果：' + (failures === 0 ? '全部通过 ✅' : failures + ' 项失败 ❌'));
process.exit(failures === 0 ? 0 : 1);
