// Model girdisinin worker'da doldurulmasının (planWindow + packWindow), eskiden ana iş parçacığında yapılan
// tek parçalı hesapla bit bit aynı tensörü verdiğini doğrular.
//   node --test mobile/test/
import assert from "node:assert/strict";
import { test } from "node:test";

import { packWindow, planWindow } from "../dl_pack.js";

const P = 72 * 72, T = 161, FS = 30, MAX_GAP = 0.35;

// v10'daki app.js dlSchedule döngüsü (referans)
function packReference(F, t0, k0) {
  const out = new Float32Array(3 * T * P);
  let j = 0;
  for (let i = 0; i < T; i++) {
    const t = t0 + (k0 + i) / FS;
    while (j < F.length - 2 && F[j + 1].t <= t) j++;
    const a = F[j], b = F[j + 1];
    if (b.t - a.t > MAX_GAP) return null;
    const w = Math.min(1, Math.max(0, (t - a.t) / (b.t - a.t || 1)));
    for (let p = 0, q = 0; p < P; p++, q += 3) {
      for (let c = 0; c < 3; c++) out[c * T * P + i * P + p] = a.px[q + c] * (1 - w) + b.px[q + c] * w;
    }
  }
  return out;
}

function packNew(F, t0, k0) {
  const plan = planWindow(F, t0, k0, T, FS, MAX_GAP);
  if (!plan) return null;
  return packWindow(F.slice(plan.lo, plan.hi + 1).map((f) => f.px), plan.ia, plan.w, T, P);
}

// Telefon kamerası gibi düzensiz aralıklı kareler (ortalama ~28 fps), sabit tohumlu rastgele
function frames(n, seed, gapAt = -1) {
  let s = seed;
  const rnd = () => ((s = (s * 1664525 + 1013904223) >>> 0) / 2 ** 32);
  const F = [];
  let t = 3.217;
  for (let i = 0; i < n; i++) {
    t += 1 / 28 + (rnd() - 0.5) * 0.02 + (i === gapAt ? 0.5 : 0);
    F.push({ t, px: Uint8Array.from({ length: P * 3 }, () => (rnd() * 256) | 0) });
  }
  return F;
}

test("worker paketlemesi eski hesapla bit bit aynı", () => {
  for (const seed of [1, 7, 42]) {
    const F = frames(360, seed), t0 = F[0].t;
    for (const k0 of [0, 80, 160]) {
      const ref = packReference(F, t0, k0), got = packNew(F, t0, k0);
      assert.ok(ref && got);
      assert.equal(got.length, ref.length);
      assert.ok(got.every((v, i) => Object.is(v, ref[i])), `seed ${seed}, k0 ${k0}`);
    }
  }
});

test("pencerenin başı bellekteki ilk kareden önceyse de aynı (ilk kareye sabitlenir)", () => {
  const F = frames(300, 3), t0 = F[0].t - 0.4;
  const ref = packReference(F, t0, 0), got = packNew(F, t0, 0);
  assert.ok(got.every((v, i) => Object.is(v, ref[i])));
});

test("kare boşluğu olan pencere ikisinde de atlanır", () => {
  const F = frames(300, 5, 100), t0 = F[0].t;
  assert.equal(packReference(F, t0, 0), null);
  assert.equal(packNew(F, t0, 0), null);
  assert.ok(packNew(F, t0, 160));   // boşluktan sonraki pencere çalışır
});

test("yalnızca pencerenin karelerini seçer", () => {
  const F = frames(360, 9), plan = planWindow(F, F[0].t, 160, T, FS, MAX_GAP);
  assert.ok(plan.lo > 0 && plan.hi < F.length - 1);
  assert.ok(plan.hi - plan.lo + 1 <= T + 10);
});
