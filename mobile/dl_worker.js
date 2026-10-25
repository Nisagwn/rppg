// Derin öğrenme çıkarımı (ayrı iş parçacığı, arayüzü dondurmaz).
// Model: FactorizePhys (rPPG-Toolbox, NeurIPS 2024), 5. tur: MCD-rPPG + UBFC + PURE ile ince ayarlı (son epoch), ONNX'e çevrilmiş.
// Uygulama içi doğrulamada 3. tur ve 7E (MMRPhys) ile anlamlı fark yok; çevrimdışı telefon/USB testinde en iyisi (1.64 BPM).
// Girdi:  [1, 3, 161, 72, 72] float32, 0–255 ham RGB yüz kırpıntıları (30 fps; son kare tekrarlı, model içinde fark alınır)
// Çıktı:  [1, 160] nabız dalgası (BVP)
// Arka uç: "wasm" (işlemci, varsayılan) ya da "webgpu" (ekran kartı). WebGPU paketi ~27 MB ve yalnızca istenince yüklenir;
// app.js ikisini kısa bir denemeyle (bench_ms) karşılaştırıp hızlı olanı seçer. İki arka ucun çıktısı aynı
// (test/webgpu_check.mjs: korelasyon 0.99999999, en büyük fark 0.0006).
import { packWindow } from "./dl_pack.js";

// Çok iş parçacığı SharedArrayBuffer ister; sayfa service worker'ın eklediği COOP/COEP başlıklarıyla yalıtılmışsa
// açılır (bkz. sw.js), değilse tek iş parçacığı. Yüz bulucu ve kamera için bir çekirdek boş bırakılır.
const THREADS = self.crossOriginIsolated ? Math.max(1, Math.min(4, (navigator.hardwareConcurrency || 2) - 1)) : 1;
const T = 161, SIZE = 72;

let ort = null, session = null;

async function load(ep) {
  const t0 = performance.now();
  ort = await import(ep === "webgpu" ? "./vendor/ort/ort.webgpu.bundle.min.mjs" : "./vendor/ort/ort.wasm.bundle.min.mjs");
  ort.env.wasm.numThreads = THREADS;
  ort.env.wasm.wasmPaths = new URL("./vendor/ort/", import.meta.url).href;
  if (ep === "webgpu" && !(await navigator.gpu?.requestAdapter())) throw new Error("WebGPU yok");
  session = await ort.InferenceSession.create(new URL("./model/factorizephys.onnx", import.meta.url).href,
    { executionProviders: [ep], graphOptimizationLevel: "all" });
  return performance.now() - t0;
}

async function infer(frames) {
  const out = await session.run({ video: new ort.Tensor("float32", frames, [1, 3, T, SIZE, SIZE]) });
  return Float32Array.from(out.bvp.data);
}

// Isınma (WebGPU'da gölgelendirici derlemesi) + bir ölçülü çalıştırma: arka uçların karşılaştırılması için.
// Girdi gerçek kareye benzer gürültülü bir görüntü: sabit girdide kare farkları sıfır, model içinde denormal sayılar
// oluşuyor ve wasm 50 kat yavaşlıyordu (12.5 s), karşılaştırma anlamsızlaşıyordu.
async function bench() {
  const x = new Float32Array(3 * T * SIZE * SIZE);
  for (let i = 0, s = 1; i < x.length; i++) { s = (s * 16807) % 2147483647; x[i] = 100 + 60 * (s / 2147483647); }
  await infer(x.slice());
  const t0 = performance.now();
  await infer(x);
  return performance.now() - t0;
}

self.onmessage = async (e) => {
  const msg = e.data;
  try {
    if (msg.type === "load") {
      const ep = msg.ep || "wasm";
      const ms = await load(ep);
      const benchMs = msg.bench ? await bench() : 0;
      self.postMessage({ type: "ready", ms, proto: 2, threads: THREADS, ep, bench_ms: benchMs });   // proto 2: kırpıntı + plan (v11+)
    } else if (msg.type === "run") {
      // Ana iş parçacığı yalnızca kırpıntıları ve enterpolasyon planını gönderir; tensör burada doldurulur.
      // Sürüm geçişinde (service worker yeni worker'ı eski sayfaya verir) eski sayfa hazır tensör gönderir.
      const frames = msg.frames || packWindow(msg.px, msg.ia, msg.w, msg.T, SIZE * SIZE);
      const t0 = performance.now();
      const bvp = await infer(frames);
      self.postMessage({ type: "bvp", k0: msg.k0, gen: msg.gen, bvp, ms: performance.now() - t0 }, [bvp.buffer]);
    }
  } catch (err) {
    self.postMessage({ type: "error", message: String(err?.message || err) });
  }
};
