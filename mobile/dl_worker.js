// Derin öğrenme çıkarımı (ayrı iş parçacığı, arayüzü dondurmaz).
// Model: FactorizePhys (rPPG-Toolbox, NeurIPS 2024), MCD-rPPG + UBFC + PURE ile ince ayarlı, ONNX'e çevrilmiş.
// Girdi:  [1, 3, 161, 72, 72] float32, 0–255 ham RGB yüz kırpıntıları (30 fps; son kare tekrarlı, model içinde fark alınır)
// Çıktı:  [1, 160] nabız dalgası (BVP)
import * as ort from "./vendor/ort/ort.wasm.bundle.min.mjs";

ort.env.wasm.numThreads = 1;              // GitHub Pages çapraz köken yalıtımı sunmuyor: tek iş parçacığı
ort.env.wasm.wasmPaths = new URL("./vendor/ort/", import.meta.url).href;

let session = null;

async function load() {
  const t0 = performance.now();
  session = await ort.InferenceSession.create(new URL("./model/factorizephys.onnx", import.meta.url).href,
    { executionProviders: ["wasm"], graphOptimizationLevel: "all" });
  return performance.now() - t0;
}

self.onmessage = async (e) => {
  const msg = e.data;
  try {
    if (msg.type === "load") {
      const ms = await load();
      self.postMessage({ type: "ready", ms });
    } else if (msg.type === "run") {
      const t0 = performance.now();
      const input = new ort.Tensor("float32", msg.frames, [1, 3, msg.T, 72, 72]);
      const out = await session.run({ video: input });
      const bvp = Float32Array.from(out.bvp.data);
      self.postMessage({ type: "bvp", k0: msg.k0, gen: msg.gen, bvp, ms: performance.now() - t0 }, [bvp.buffer]);
    }
  } catch (err) {
    self.postMessage({ type: "error", message: String(err?.message || err) });
  }
};
