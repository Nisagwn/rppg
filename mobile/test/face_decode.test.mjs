// YuNet kod çözümünün (face_decode.js) OpenCV FaceDetectorYN formülleriyle aynı sonucu verdiğini,
// örtüşen kutuların ayıklandığını ve pico eşdeğeri kutuya dönüşümü doğrular.
//   node --test mobile/test/
import assert from "node:assert/strict";
import { test } from "node:test";

import { decodeYunet, iou, yunetToBox } from "../face_decode.js";

// pw x ph girdisi için boş YuNet çıktıları; set(adım, satır, sütun, ...) bir hücreyi doldurur
function outputs(pw, ph) {
  const o = {};
  for (const s of [8, 16, 32]) {
    const n = (pw / s) * (ph / s);
    o[`cls_${s}`] = new Float32Array(n); o[`obj_${s}`] = new Float32Array(n);
    o[`bbox_${s}`] = new Float32Array(4 * n); o[`kps_${s}`] = new Float32Array(10 * n);
  }
  const set = (s, r, c, cls, obj, bb) => {
    const i = r * (pw / s) + c;
    o[`cls_${s}`][i] = cls; o[`obj_${s}`][i] = obj; o[`bbox_${s}`].set(bb, 4 * i);
    o[`kps_${s}`].set([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0], 10 * i);
  };
  return { get: (n) => o[n], set };
}

test("kod çözme OpenCV formülüyle aynı", () => {
  const { get, set } = outputs(320, 256);
  set(16, 5, 7, 0.81, 1.0, [0.5, 0.25, Math.log(4), Math.log(5)]);   // puan sqrt(0.81·1) = 0.9
  const f = decodeYunet(get, 320, 256, 0.5);
  assert.equal(f.length, 1);
  const cx = (7 + 0.5) * 16, cy = (5 + 0.25) * 16, w = 4 * 16, h = 5 * 16;
  assert.ok(Math.abs(f[0].s - 0.9) < 1e-6);
  for (const [k, v] of Object.entries({ x: cx - w / 2, y: cy - h / 2, w, h })) assert.ok(Math.abs(f[0][k] - v) < 1e-4, k);
  assert.ok(Math.abs(f[0].kps[0] - (7 + 0.1) * 16) < 1e-4 && Math.abs(f[0].kps[1] - (5 + 0.2) * 16) < 1e-4);
});

test("eşik altı elenir, örtüşen kutulardan puanı yüksek olan kalır", () => {
  const { get, set } = outputs(320, 256);
  set(8, 10, 10, 0.95, 0.95, [0, 0, Math.log(8), Math.log(8)]);    // 64 px kutu, puan 0.95
  set(8, 10, 11, 0.8, 0.8, [0, 0, Math.log(8), Math.log(8)]);      // 8 px kaymış aynı yüz, puan 0.8
  set(32, 1, 1, 0.3, 0.3, [0, 0, 0, 0]);                           // puan 0.3 < eşik
  const f = decodeYunet(get, 320, 256, 0.5);
  assert.equal(f.length, 1);
  assert.ok(Math.abs(f[0].s - 0.95) < 1e-6);
});

test("iou ve pico eşdeğeri kare kutu", () => {
  assert.equal(iou({ x: 0, y: 0, w: 10, h: 10 }, { x: 0, y: 0, w: 10, h: 10 }), 1);
  assert.equal(iou({ x: 0, y: 0, w: 10, h: 10 }, { x: 20, y: 0, w: 10, h: 10 }), 0);
  const b = yunetToBox({ x: 100, y: 50, w: 80, h: 120 }, { dx: 0.1, dy: -0.05, k: 1.2 });
  const size = 1.2 * Math.sqrt(80 * 120);
  assert.ok(Math.abs(b.w - size) < 1e-9 && b.w === b.h);
  assert.ok(Math.abs(b.x + b.w / 2 - (140 + 8)) < 1e-9 && Math.abs(b.y + b.h / 2 - (110 - 6)) < 1e-9);
});
