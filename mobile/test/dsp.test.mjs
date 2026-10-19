// JS sinyal işleme kütüphanesinin Python paketiyle aynı sonucu verdiğini doğrular.
//   node --test mobile/test/
// fixture_python.json, rppg/ paketiyle sentetik videodan üretilmiştir.
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

import {
  BPM_GRID, OnlineHRTracker, bandpass, detrendTarvainen, peakBpm, pos, preprocessBvp,
  resampleUniform, spectrumBpm,
} from "../dsp.js";

const fx = JSON.parse(readFileSync(new URL("./fixture_python.json", import.meta.url)));

const maxAbsDiff = (a, b) => Math.max(...a.map((v, i) => Math.abs(v - b[i])));
const corr = (a, b) => {
  const n = a.length, ma = a.reduce((s, v) => s + v, 0) / n, mb = b.reduce((s, v) => s + v, 0) / n;
  let sab = 0, saa = 0, sbb = 0;
  for (let i = 0; i < n; i++) {
    sab += (a[i] - ma) * (b[i] - mb);
    saa += (a[i] - ma) ** 2;
    sbb += (b[i] - mb) ** 2;
  }
  return sab / Math.sqrt(saa * sbb);
};

test("POS Python ile aynı", () => {
  assert.ok(maxAbsDiff(pos(fx.rgb), fx.pos) < 1e-9);
});

test("Tarvainen detrend Python ile aynı", () => {
  assert.ok(maxAbsDiff(detrendTarvainen(fx.pos), fx.detrend) < 1e-7);
});

test("Butterworth sosfiltfilt Python ile aynı", () => {
  assert.ok(maxAbsDiff(bandpass(fx.detrend), fx.bandpass) < 1e-9);
});

test("BVP ve spektrum Python ile aynı, nabız doğru", () => {
  const bvp = preprocessBvp(fx.pos);
  assert.ok(corr(bvp, fx.bvp) > 0.9999);
  const spec = spectrumBpm(bvp);
  assert.ok(corr(spec, fx.spec) > 0.999);
  const hr = peakBpm(BPM_GRID, spec);
  assert.ok(Math.abs(hr - fx.hr) < 0.3, `JS ${hr} / Python ${fx.hr}`);
  assert.ok(Math.abs(hr - fx.true_hr) < 2, `JS ${hr} / gerçek ${fx.true_hr}`);
});

test("çevrimiçi takipçi Python ile aynı", () => {
  const trk = new OnlineHRTracker();
  const spec = spectrumBpm(preprocessBvp(fx.pos));
  const hrs = [1, 2, 3].map(() => trk.update(spec, 1, 1));
  hrs.forEach((h, i) => assert.ok(Math.abs(h - fx.tracker[i]) < 0.3));
});

test("takipçi tek pencerelik sahte tepeyi yok sayar", () => {
  const peak = (bpm) => BPM_GRID.map((g) => Math.exp(-0.5 * ((g - bpm) / 2) ** 2));
  const trk = new OnlineHRTracker();
  for (let i = 0; i < 8; i++) trk.update(peak(72), 1, 1);
  const h = trk.update(peak(140), 1, 1);
  assert.ok(Math.abs(h - 72) < 3, `sahte tepeye atladı: ${h}`);
});

test("düzensiz zaman damgalarını 30 Hz'e yeniden örnekler", () => {
  const t = [], x = [];
  let tt = 0;
  for (let i = 0; i < 400; i++) {
    tt += 1 / 30 + (i % 3 === 0 ? 0.01 : -0.004);
    t.push(tt);
    x.push(Math.sin(2 * Math.PI * 1.2 * tt));
  }
  const u = resampleUniform(t, x, 30);
  const hr = peakBpm(BPM_GRID, spectrumBpm(u));
  assert.ok(Math.abs(hr - 72) < 1, `${hr}`);
});

test("sıçrama payıyla takipçi kalıcı yanlış tepeden kurtulur, payı 0 iken kurtulamaz", () => {
  // Yanlış tepe kaybolmuyor, yalnızca zayıflıyor (ör. ışık titremesi, hareket); gerçek nabız 2 kat güçlü.
  const g = (bpm) => BPM_GRID.map((x) => Math.exp(-0.5 * ((x - bpm) / 2) ** 2));
  const both = (a120, a75) => g(120).map((v, i) => a120 * v + a75 * g(75)[i] + 0.02);
  const run = (jump) => {
    const trk = new OnlineHRTracker(BPM_GRID, 4, jump);
    for (let i = 0; i < 10; i++) trk.update(both(1, 0), 1, 1);       // başta yalnızca yanlış tepe
    let h = 0;
    for (let i = 0; i < 20; i++) h = trk.update(both(0.5, 1), 1, 1); // 20 s boyunca gerçek nabız baskın
    return h;
  };
  assert.ok(Math.abs(run(0.05) - 75) < 3, `kurtulamadı: ${run(0.05)}`);
  assert.ok(Math.abs(run(0) - 120) < 3, `payı 0 iken de kurtuldu: ${run(0)}`);
});
