// Çevrimdışı çalışma: uygulama dosyalarını önbellekten sun, arka planda güncelle.
const CACHE = "rppg-v8";
const FILES = ["./", "index.html", "style.css", "app.js", "dsp.js", "manifest.webmanifest",
  "vendor/pico.js", "vendor/facefinder", "icons/icon.svg", "icons/icon-192.png", "icons/icon-512.png",
  "dl_worker.js", "model/factorizephys.onnx", "vendor/ort/ort.wasm.bundle.min.mjs", "vendor/ort/ort-wasm-simd-threaded.wasm", "vendor/ort/ort-wasm-simd-threaded.mjs"];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(FILES.map((f) => new Request(f, { cache: "reload" })))).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys()
    .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
    .then(() => self.clients.claim()));
});

self.addEventListener("fetch", (e) => {
  if (e.request.method !== "GET" || new URL(e.request.url).origin !== location.origin) return;
  e.respondWith(caches.open(CACHE).then(async (c) => {
    const hit = await c.match(e.request);
    const net = fetch(e.request).then((r) => {
      if (r.ok) c.put(e.request, r.clone());
      return r;
    }).catch(() => hit);
    return hit || net;
  }));
});
