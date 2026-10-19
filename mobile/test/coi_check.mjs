// Yayındaki sitenin service worker üzerinden çapraz köken yalıtımına (çok iş parçacıklı model) geçtiğini denetler.
// Testlerdeki ?autotest sayfası service worker kaydetmez; bu betik siteyi normal kullanıcı gibi açar:
//   node mobile/test/coi_check.mjs [--url https://nisagwn.github.io/rppg/]
import { spawn } from "node:child_process";
import { existsSync, mkdtempSync } from "node:fs";
import { createServer } from "node:net";
import { tmpdir } from "node:os";
import { join } from "node:path";

const i = process.argv.indexOf("--url");
const url = i > 0 ? process.argv[i + 1] : "https://nisagwn.github.io/rppg/";
const chrome = process.env.CHROME || ["C:/Program Files/Google/Chrome/Application/chrome.exe",
  "/usr/bin/google-chrome", "/usr/bin/chromium"].find(existsSync);
const port = await new Promise((r) => { const s = createServer().listen(0, "127.0.0.1", () => { const p = s.address().port; s.close(() => r(p)); }); });
const proc = spawn(chrome, ["--headless=new", "--disable-gpu", `--remote-debugging-port=${port}`,
  `--user-data-dir=${mkdtempSync(join(tmpdir(), "rppg-coi-"))}`, url], { stdio: "ignore" });
const wait = (ms) => new Promise((r) => setTimeout(r, ms));
let ws;
for (let k = 0; k < 50 && !ws; k++) {
  await wait(200);
  try {
    const page = (await (await fetch(`http://127.0.0.1:${port}/json`)).json()).find((t) => t.type === "page");
    if (page) ws = new WebSocket(page.webSocketDebuggerUrl);
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
for (let k = 0; k < 30; k++) {   // service worker kurulur, sayfa kendini bir kez yeniler
  await wait(1000);
  res = await evaluate("({ coi: self.crossOriginIsolated, sw: !!navigator.serviceWorker?.controller, v: document.getElementById('version')?.textContent })");
  if (res?.coi) break;
}
console.log(JSON.stringify(res));
proc.kill();
process.exit(res?.coi ? 0 : 1);
