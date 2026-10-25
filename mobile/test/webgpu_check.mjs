// WebGPU arka ucunun modeli wasm ile aynı sonuçla çalıştırıp çalıştırmadığını denetler (doğruluk; hız telefonda ölçülür).
// Aynı rastgele girdi iki oturumdan geçer: ["wasm"] ve ["webgpu"]; en büyük fark ve korelasyon yazdırılır.
//   node mobile/test/webgpu_check.mjs [--gpu]     # --gpu: gerçek ekran kartı (varsayılan: SwiftShader, işlemcide WebGPU)
import { spawn } from "node:child_process";
import { existsSync, mkdtempSync, readFileSync } from "node:fs";
import { createServer } from "node:http";
import { tmpdir } from "node:os";
import { extname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = fileURLToPath(new URL("..", import.meta.url));
const chrome = process.env.CHROME || ["C:/Program Files/Google/Chrome/Application/chrome.exe",
  "/usr/bin/google-chrome", "/usr/bin/chromium"].find(existsSync);
const types = { ".html": "text/html", ".js": "text/javascript", ".mjs": "text/javascript", ".wasm": "application/wasm" };
const page = `<!doctype html><meta charset="utf-8"><script type="module">
import * as ort from "/vendor/ort/ort.webgpu.bundle.min.mjs";
ort.env.wasm.wasmPaths = "/vendor/ort/";
const T = 161, n = 3 * T * 72 * 72, x = new Float32Array(n);
let s = 1; for (let i = 0; i < n; i++) { s = (s * 16807) % 2147483647; x[i] = 100 + 60 * (s / 2147483647) + 20 * Math.sin(i / 5000); }
const run = async (ep) => {
  const ses = await ort.InferenceSession.create("/model/factorizephys.onnx", { executionProviders: [ep], graphOptimizationLevel: "all" });
  const inp = () => new ort.Tensor("float32", x.slice(), [1, 3, T, 72, 72]);
  await ses.run({ video: inp() });                       // ısınma (gölgelendirici derlemesi)
  const t0 = performance.now(), out = await ses.run({ video: inp() });
  return { y: Array.from(out.bvp.data), ms: performance.now() - t0 };
};
try {
  const adapter = await navigator.gpu?.requestAdapter();
  const a = await run("wasm"), b = await run("webgpu");
  const m = (v) => v.reduce((p, q) => p + q, 0) / v.length, ma = m(a.y), mb = m(b.y);
  let sab = 0, saa = 0, sbb = 0, dmax = 0;
  a.y.forEach((v, i) => { const p = v - ma, q = b.y[i] - mb; sab += p * q; saa += p * p; sbb += q * q; dmax = Math.max(dmax, Math.abs(v - b.y[i])); });
  window.__res = { adapter: adapter?.info?.description || adapter?.info?.vendor || String(!!adapter), wasm_ms: a.ms, webgpu_ms: b.ms,
    max_fark: dmax, olcek: Math.sqrt(saa / a.y.length), korelasyon: sab / Math.sqrt(saa * sbb) };
} catch (e) { window.__res = { hata: String(e?.message || e) }; }
</script>`;
const server = createServer((req, res) => {
  const path = decodeURIComponent(new URL(req.url, "http://x").pathname);
  const h = { "cross-origin-opener-policy": "same-origin", "cross-origin-embedder-policy": "require-corp" };
  if (path === "/check.html") { res.writeHead(200, { "content-type": "text/html", ...h }); return res.end(page); }
  const p = join(root, path);
  if (!p.startsWith(root) || !existsSync(p)) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { "content-type": types[extname(p)] || "application/octet-stream", ...h });
  res.end(readFileSync(p));
});
await new Promise((r) => server.listen(0, "127.0.0.1", r));
const freePort = () => new Promise((r) => { const s = createServer().listen(0, "127.0.0.1", () => { const p = s.address().port; s.close(() => r(p)); }); });
const debugPort = await freePort();
const gpu = process.argv.includes("--gpu") ? [] : ["--use-webgpu-adapter=swiftshader", "--enable-unsafe-swiftshader"];
const proc = spawn(chrome, ["--headless=new", "--enable-unsafe-webgpu", ...gpu, `--remote-debugging-port=${debugPort}`,
  `--user-data-dir=${mkdtempSync(join(tmpdir(), "rppg-gpu-"))}`, `http://127.0.0.1:${server.address().port}/check.html`], { stdio: "ignore" });
const wait = (ms) => new Promise((r) => setTimeout(r, ms));
let ws;
for (let k = 0; k < 50 && !ws; k++) {
  await wait(200);
  try {
    const t = (await (await fetch(`http://127.0.0.1:${debugPort}/json`)).json()).find((x) => x.type === "page");
    if (t) ws = new WebSocket(t.webSocketDebuggerUrl);
  } catch { /* Chrome açılıyor */ }
}
await new Promise((r) => ws.addEventListener("open", r, { once: true }));
let id = 0;
const pending = new Map();
ws.addEventListener("message", (e) => { const m = JSON.parse(e.data); pending.get(m.id)?.(m); });
const evaluate = (expression) => new Promise((r) => {
  const n = ++id;
  pending.set(n, (m) => r(m.result?.result?.value));
  ws.send(JSON.stringify({ id: n, method: "Runtime.evaluate", params: { expression, returnByValue: true } }));
});
let res;
for (let k = 0; k < 180 && !res; k++) { await wait(1000); res = await evaluate("window.__res"); }
console.log(JSON.stringify(res));
proc.kill();
server.close();
process.exit(res && !res.hata && res.korelasyon > 0.999 ? 0 : 1);
