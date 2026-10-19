// USB ile bağlı Android telefondaki Chrome'da açık uygulamayı canlı izler (adb + Chrome DevTools protokolü).
// Önce: telefonda USB hata ayıklama açık, Chrome'da uygulama açık; sonra
//   adb forward tcp:9333 localabstract:chrome_devtools_remote
//   node mobile/test/phone_watch.mjs [--port 9333] [--saniye 300] [--log telefon.jsonl]
// Her 2 saniyede bir: sürüm, yalıtım, model iş parçacığı ve süresi, kare hızı, durum, nabız, son teşhis satırı.
import { appendFileSync } from "node:fs";

const arg = (k, d) => { const i = process.argv.indexOf(`--${k}`); return i > 0 ? process.argv[i + 1] : d; };
const port = Number(arg("port", 9333)), sure = Number(arg("saniye", 300)), logf = arg("log", "");
const wait = (ms) => new Promise((r) => setTimeout(r, ms));

const tabs = await (await fetch(`http://127.0.0.1:${port}/json`)).json();
const tab = tabs.find((t) => t.type === "page" && /nisagwn\.github\.io\/rppg|127\.0\.0\.1|localhost/.test(t.url));
if (!tab) {
  console.log("Uygulama sekmesi bulunamadı. Açık sekmeler:", tabs.map((t) => t.url).join(" | "));
  process.exit(1);
}
console.log("bağlandı:", tab.url);
const ws = new WebSocket(tab.webSocketDebuggerUrl);
await new Promise((r) => ws.addEventListener("open", r, { once: true }));
let id = 0;
const pending = new Map();
ws.addEventListener("message", (e) => {
  const m = JSON.parse(e.data);
  if (m.id) pending.get(m.id)?.(m);
  else if (m.method === "Runtime.exceptionThrown") console.log("HATA:", m.params.exceptionDetails?.exception?.description || m.params.exceptionDetails?.text);
  else if (m.method === "Runtime.consoleAPICalled" && ["error", "warning"].includes(m.params.type))
    console.log(`konsol ${m.params.type}:`, m.params.args.map((a) => a.value ?? a.description).join(" "));
});
const send = (method, params = {}) => new Promise((r) => { const n = ++id; pending.set(n, r); ws.send(JSON.stringify({ id: n, method, params })); });
await send("Runtime.enable");
const expr = `(() => { const s = window.__rppg, d = window.__rppgDl, q = window.__rppgQuick, $ = (i) => document.getElementById(i)?.textContent;
  return { v: $("version"), coi: self.crossOriginIsolated, cores: navigator.hardwareConcurrency, run: s?.running, mode: s?.mode,
    quick: q?.phase || "", threads: d?.threads, model_ms: Math.round(d?.ms || 0), ready: d?.ready, failed: d?.failed,
    fps: $("fps"), status: document.querySelector("#status span")?.textContent, hr: $("hr"),
    diag: s?.diag?.at(-1), kirpinti: d?.frames?.length, kayit: s?.log?.length }; })()`;
const t0 = Date.now();
while ((Date.now() - t0) / 1000 < sure) {
  const r = await send("Runtime.evaluate", { expression: expr, returnByValue: true });
  const v = r.result?.result?.value;
  if (v) {
    const g = v.diag || {};
    console.log(`${new Date().toLocaleTimeString()} ${v.v} coi=${v.coi} çekirdek=${v.cores} iş=${v.threads} model=${v.model_ms}ms ` +
      `| ${v.fps} | ${v.run ? (v.quick ? "hızlı:" + v.quick : "canlı") : "durdu"} | nabız ${v.hr} | ${v.status} ` +
      `| kare ${g.frames ?? "-"} yüz ${g.face ?? "-"} durak ${g.gate ?? "-"} yunet ${g.yunet ?? "-"}` + (v.failed ? ` | MODEL HATASI: ${v.failed}` : ""));
    if (logf) appendFileSync(logf, JSON.stringify({ t: Date.now(), ...v }) + "\n");
  }
  await wait(2000);
}
ws.close();
