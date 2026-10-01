// Uçtan uca tarayıcı testi: uygulamayı yerel sunucuda açar, Chrome'a y4m dosyasını sahte kamera
// olarak verir, ölçülen nabzı beklenen değerle karşılaştırır ve ekran görüntüsü kaydeder.
//
//   node mobile/test/e2e.mjs --video yuz_84bpm.y4m --expect 84 [--mode finger] [--seconds 35] [--shot out.png]
//                            [--url https://nisagwn.github.io/rppg/]   # yayındaki sürümü test et
//                            [--kamera arka]                           # yüz modunda arka kamera seçimi
//
// Chrome yolu: CHROME ortam değişkeni ya da Windows/Linux/macOS varsayılanları.
import { spawn } from "node:child_process";
import { existsSync, mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { createServer } from "node:http";
import { tmpdir } from "node:os";
import { extname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const args = {};
for (let i = 2, argv = process.argv; i < argv.length; i++) {
  if (!argv[i].startsWith("--")) continue;
  const next = argv[i + 1];
  args[argv[i].slice(2)] = next === undefined || next.startsWith("--") ? true : (i++, next);
}
const video = resolve(args.video), expect = Number(args.expect), mode = args.mode || "face";
const seconds = Number(args.seconds || 35);
const root = fileURLToPath(new URL("..", import.meta.url));

const chrome = process.env.CHROME || [
  "C:/Program Files/Google/Chrome/Application/chrome.exe",
  "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
  "/usr/bin/google-chrome", "/usr/bin/chromium",
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
].find(existsSync);
if (!chrome) throw new Error("Chrome bulunamadı; CHROME ortam değişkenini ayarlayın");

const types = { ".html": "text/html", ".js": "text/javascript", ".css": "text/css", ".png": "image/png",
  ".svg": "image/svg+xml", ".webmanifest": "application/manifest+json", ".json": "application/json" };
const server = createServer((req, res) => {
  const p = join(root, decodeURIComponent(new URL(req.url, "http://x").pathname).replace(/\/$/, "/index.html"));
  if (!p.startsWith(root) || !existsSync(p)) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { "content-type": types[extname(p)] || "application/octet-stream" });
  res.end(readFileSync(p));
});
await new Promise((r) => server.listen(0, "127.0.0.1", r));
const port = server.address().port, debugPort = 9300 + Math.floor(Math.random() * 500);

const proc = spawn(chrome, [
  "--headless=new", `--remote-debugging-port=${debugPort}`, `--user-data-dir=${mkdtempSync(join(tmpdir(), "rppg-"))}`,
  "--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream", `--use-file-for-fake-video-capture=${video}`,
  "--autoplay-policy=no-user-gesture-required", "--window-size=412,915", "--no-first-run", "--no-default-browser-check",
  `${args.url || `http://127.0.0.1:${port}/index.html`}?autotest=${mode}${args.kamera ? `&kamera=${args.kamera}` : ""}`,
], { stdio: "ignore" });

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let wsUrl;
for (let i = 0; i < 50 && !wsUrl; i++) {
  await sleep(200);
  try {
    const list = await (await fetch(`http://127.0.0.1:${debugPort}/json`)).json();
    wsUrl = list.find((t) => t.type === "page" && t.url.includes("autotest"))?.webSocketDebuggerUrl;
  } catch { /* Chrome henüz açılmadı */ }
}
if (!wsUrl) throw new Error("Chrome hata ayıklama bağlantısı kurulamadı");

const ws = new WebSocket(wsUrl);
await new Promise((r) => ws.addEventListener("open", r, { once: true }));
let id = 0;
const pending = new Map();
ws.addEventListener("message", (e) => {
  const m = JSON.parse(e.data);
  if (pending.has(m.id)) { pending.get(m.id)(m.result); pending.delete(m.id); }
});
const cdp = (method, params = {}) => new Promise((r) => { pending.set(++id, r); ws.send(JSON.stringify({ id, method, params })); });
const evaluate = async (expr) => (await cdp("Runtime.evaluate", { expression: expr, returnByValue: true })).result.value;

await sleep(seconds * 1000);
const log = await evaluate("window.__rppg.log");
const cam = await evaluate("({ facing: window.__rppg.facing, mirror: document.getElementById('stage').classList.contains('mirror'), " +
  "label: document.getElementById('flip-label').textContent, csvCam: window.__rppg.log.at(-1)?.cam })");
const status = await evaluate("document.querySelector('#status span').textContent");
if (args.shot) {
  const { data } = await cdp("Page.captureScreenshot", { format: "png", captureBeyondViewport: true });
  writeFileSync(args.shot, Buffer.from(data, "base64"));
}
ws.close();
proc.kill();
server.close();

const last = log.slice(-15).map((r) => r.hr).sort((a, b) => a - b);
const median = last[Math.floor(last.length / 2)];
console.log(JSON.stringify({ mode, expect, windows: log.length, median_last15: median,
  hr: log.map((r) => +r.hr.toFixed(1)), snr_last: log.at(-1)?.snr.toFixed(1), status, cam }, null, 1));
if (args.log) writeFileSync(args.log, JSON.stringify(log));
const ok = log.length >= 10 && Math.abs(median - expect) < 3;
console.log(ok ? "BAŞARILI" : "BAŞARISIZ");
process.exit(ok ? 0 : 1);
