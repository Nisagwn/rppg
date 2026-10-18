// Yüz tespiti (ayrı iş parçacığı): YuNet (Wu vd. 2023, "YuNet: A Tiny Millisecond-level Face Detector";
// OpenCV Zoo, MIT lisansı, 230 KB, ~75 bin parametre). pico'nun bulamadığı yan açılı / döndürülmüş yüzleri bulur.
// Girdi:  küçültülmüş kare (RGBA), Çıktı: puanı eşiği geçen yüzler [{ s, x, y, w, h, kps }] (girdi pikseli cinsinden).
// Kod çözme OpenCV FaceDetectorYN ile aynı (ızgara adımları 8/16/32, çapasız): merkez = (hücre + d) · adım, boyut = e^d · adım.
import * as ort from "./vendor/ort/ort.wasm.bundle.min.mjs";
import { decodeYunet } from "./face_decode.js";

ort.env.wasm.numThreads = 1;
ort.env.wasm.wasmPaths = new URL("./vendor/ort/", import.meta.url).href;

let session = null;

self.onmessage = async (e) => {
  const m = e.data;
  try {
    if (m.type === "load") {
      session = await ort.InferenceSession.create(new URL("./vendor/yunet/face_detection_yunet_2026may.onnx", import.meta.url).href,
        { executionProviders: ["wasm"], graphOptimizationLevel: "all" });
      self.postMessage({ type: "ready" });
    } else if (m.type === "detect") {
      const t0 = performance.now();
      const { w, h } = m, d = new Uint8ClampedArray(m.rgba);
      const pw = Math.ceil(w / 32) * 32, ph = Math.ceil(h / 32) * 32, P = pw * ph;
      const x = new Float32Array(3 * P);            // NCHW, BGR, 0–255, sağ/alt kenar sıfır dolgulu (OpenCV gibi)
      for (let r = 0; r < h; r++) {
        for (let c = 0; c < w; c++) {
          const i = (r * w + c) * 4, k = r * pw + c;
          x[k] = d[i + 2]; x[P + k] = d[i + 1]; x[2 * P + k] = d[i];
        }
      }
      const out = await session.run({ input: new ort.Tensor("float32", x, [1, 3, ph, pw]) });
      const get = (n) => out[n].data;
      const faces = decodeYunet(get, pw, ph, m.thr ?? 0.5);
      self.postMessage({ type: "faces", id: m.id, faces, ms: performance.now() - t0 });
    }
  } catch (err) {
    self.postMessage({ type: "error", id: m.id, message: String(err?.message || err) });
  }
};
