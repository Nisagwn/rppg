// YuNet çıktısının kod çözümü (face_worker.js) ve YuNet kutusunun pico kutusuna dönüştürülmesi (app.js).
// Saf fonksiyonlar: node testlerinde de çalışır.

// get(ad) -> Float32Array; pw, ph: modele verilen (32'nin katı) boyut. Dönüş puana göre azalan sırada,
// örtüşenleri ayıklanmış (NMS, IoU > 0.3) yüzler.
export function decodeYunet(get, pw, ph, thr = 0.5) {
  const faces = [];
  for (const s of [8, 16, 32]) {
    const cols = pw / s, rows = ph / s, cls = get(`cls_${s}`), obj = get(`obj_${s}`), bb = get(`bbox_${s}`), kp = get(`kps_${s}`);
    for (let i = 0; i < cols * rows; i++) {
      const sc = Math.sqrt(Math.min(1, Math.max(0, cls[i])) * Math.min(1, Math.max(0, obj[i])));
      if (sc < thr) continue;
      const r = Math.floor(i / cols), c = i - r * cols;
      const cx = (c + bb[4 * i]) * s, cy = (r + bb[4 * i + 1]) * s, w = Math.exp(bb[4 * i + 2]) * s, h = Math.exp(bb[4 * i + 3]) * s;
      const kps = [];
      for (let k = 0; k < 5; k++) kps.push((c + kp[10 * i + 2 * k]) * s, (r + kp[10 * i + 2 * k + 1]) * s);
      faces.push({ s: sc, x: cx - w / 2, y: cy - h / 2, w, h, kps });
    }
  }
  faces.sort((a, b) => b.s - a.s);
  const keep = [];
  for (const f of faces) if (keep.every((k) => iou(k, f) <= 0.3)) keep.push(f);
  return keep;
}

export function iou(a, b) {
  const ix = Math.max(0, Math.min(a.x + a.w, b.x + b.w) - Math.max(a.x, b.x));
  const iy = Math.max(0, Math.min(a.y + a.h, b.y + b.h) - Math.max(a.y, b.y));
  const inter = ix * iy;
  return inter / (a.w * a.h + b.w * b.h - inter || 1);
}

// YuNet kutusu (alından çeneye, yüz kadar dar) pico kutusundan farklı oturur. ROI kesirleri (ROI_DEFS) ve modelin
// x1.5 kırpması pico kutusuna göre ayarlı olduğundan YuNet kutusu, iki dedektörün birlikte bulduğu önden MCD
// karelerinde öğrenilmiş doğrusal eşlemeyle pico'ya eşdeğer kare kutuya çevrilir (bkz. results/mobil_yuz_tespiti).
// 5 önden webcam kesiti, 1500 eş kare (medyanlar): eşleme sonrası merkez farkı kutunun %3'ü, boyut oranı 1.00 (p10–p90 0.94–1.07).
export const YUNET_TO_PICO = { dx: -0.024, dy: -0.051, k: 1.114 };
export function yunetToBox(f, M = YUNET_TO_PICO) {
  const size = M.k * Math.sqrt(f.w * f.h);
  const cx = f.x + f.w / 2 + M.dx * f.w, cy = f.y + f.h / 2 + M.dy * f.h;
  return { x: cx - size / 2, y: cy - size / 2, w: size, h: size };
}
