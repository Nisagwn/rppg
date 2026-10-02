// rPPG Nabız — telefon uygulaması.
// Yüz modu:   ön ya da arka kamera (⇄ düğmesi) -> pico yüz tespiti (Markuš vd. 2013; piksel karşılaştırmalı karar ağaçları,
//             Viola–Jones ailesinden klasik yöntem) -> 4 ROI (alın, yanaklar, tüm yüz) + YCrCb cilt maskesi
//             -> cilt piksellerinin RGB ortalaması -> POS -> detrend + bant geçiren -> spektrum
//             -> hareket güvenli çevrimiçi Bayes takibi (Viterbi'nin çevrimiçi eşi).
//             ROI'ler ortalama füzyonla birleşir: gerçek veride (UBFC, MCD-rPPG) en iyi sonucu veren hat.
//             Yapay zekâ yöntemi (varsayılan): yüz kutusu x1.5 -> 72x72 RGB -> 30 fps ızgara -> FactorizePhys
//             (ince ayarlı, ONNX, Web Worker'da) -> örtüşen parçaların birleşimi -> aynı spektrum + takip.
// Parmak modu: arka kamera + flaş, merkez bölgenin G/R kanalı (temaslı PPG).
import {
  BPM_GRID, OnlineHRTracker, analyzeWindow, motionConfidence, preprocessBvp, spectrumBpm, windowSnr,
} from "./dsp.js";

const ROI_DEFS = {               // rppg/roi.py ROI_DEFS ile aynı (yüz kutusuna göre kesirler)
  forehead: [0.30, 0.08, 0.40, 0.17],
  left_cheek: [0.15, 0.50, 0.22, 0.22],
  right_cheek: [0.63, 0.50, 0.22, 0.22],
  full: [0.20, 0.10, 0.60, 0.80],
};
const ROI_COLORS = { forehead: "#3b82f6", left_cheek: "#f97316", right_cheek: "#22c55e", full: "#a855f7" };
const WIN_SEC = 10, MIN_SEC = 8, KEEP_SEC = 20, WORK_MAX = 480, DETECT_EVERY = 4, LOCK_AFTER_MS = 2000, RAW_MAX = 30 * 60 * 5;
/* global pico */

const $ = (id) => document.getElementById(id);
const els = {
  stage: $("stage"), video: $("video"), overlay: $("overlay"), work: $("work"),
  placeholder: $("placeholder"), placeholderText: $("placeholder-text"),
  hr: $("hr"), snr: $("snr"), conf: $("conf"), fps: $("fps"), status: $("status"),
  progressWrap: $("progress-wrap"), progress: $("progress"),
  start: $("start"), csv: $("csv"), raw: $("raw"), reset: $("reset"),
  modeFace: $("mode-face"), modeFinger: $("mode-finger"), flip: $("flip"), flipLabel: $("flip-label"),
  method: $("method"), methodAi: $("method-ai"), methodPos: $("method-pos"),
  plotBvp: $("plot-bvp"), plotSpec: $("plot-spec"), plotHist: $("plot-hist"),
};
const params = new URLSearchParams(location.search);
const VERSION = "v8";
document.getElementById("version").textContent = VERSION;

const state = {
  mode: "face", running: false, stream: null, track: null, torch: false, camLock: "", lumaHist: [], maskProb: {}, raw: [], wakeLock: null,
  samples: [], tracker: new OnlineHRTracker(), motionHist: [],
  bbox: null, lastDet: 0, frameNo: 0, prevGray: null, frameTimes: [], log: [], t0: 0, timer: null, lastBvp: null,
};
window.__rppg = state; // tarayıcı testleri ve hata ayıklama için

// Yüz modunda kamera yönü: "user" (ön) ya da "environment" (arka). Tercih tarayıcıda hatırlanır; ?kamera=arka ile de seçilir.
const FACING_KEY = "rppg.facing";
state.facing = params.get("kamera") === "arka" ? "environment" : params.get("kamera") === "on" ? "user"
  : (() => { try { return localStorage.getItem(FACING_KEY) || "user"; } catch { return "user"; } })();
// Yüz modunda yöntem: "ai" (derin öğrenme modeli) ya da "pos" (klasik). ?yontem=klasik|ai ile de seçilir.
const METHOD_KEY = "rppg.method";
state.method = params.get("yontem") === "klasik" ? "pos" : params.get("yontem") === "ai" ? "ai"
  : (() => { try { return localStorage.getItem(METHOD_KEY) || "ai"; } catch { return "ai"; } })();
const methodName = () => (state.mode === "finger" ? "parmak" : state.method === "ai" ? "yapay zekâ" : "klasik (POS)");
const camName = () => (state.mode === "finger" ? "arka (parmak)" : state.facing === "user" ? "ön" : "arka");

// ------------------------------------------------------------------ yardımcılar
function isSkin(r, g, b) {                         // rppg/roi.py skin_mask (OpenCV YCrCb eşikleri)
  const y = 0.299 * r + 0.587 * g + 0.114 * b;
  const cr = (r - y) * 0.713 + 128, cb = (b - y) * 0.564 + 128;
  return y >= 40 && y <= 240 && cr >= 133 && cr <= 173 && cb >= 77 && cb <= 127;
}

function setStatus(text, level = "") {
  els.status.className = `status ${level}`;
  els.status.querySelector("span").textContent = text;
}

// pico yüz dedektörü: kaskad bir kez yüklenir, son 5 karenin tespitleri birleştirilir.
let classifyRegion = null, detMemory = null;
async function loadFaceDetector() {
  if (classifyRegion) return;
  const bytes = new Int8Array(await (await fetch("vendor/facefinder")).arrayBuffer());
  classifyRegion = pico.unpack_cascade(bytes);
  detMemory = pico.instantiate_detection_memory(5);
}

function detectFace(d, W, H) {
  const gray = new Uint8Array(W * H);
  for (let i = 0, j = 0; i < gray.length; i++, j += 4) gray[i] = (2 * d[j] + 7 * d[j + 1] + d[j + 2]) / 10;
  const m = Math.min(W, H);
  let dets = pico.run_cascade({ pixels: gray, nrows: H, ncols: W, ldim: W }, classifyRegion,
    { shiftfactor: 0.1, minsize: Math.max(20, 0.1 * m), maxsize: m, scalefactor: 1.1 });
  dets = pico.cluster_detections(detMemory(dets), 0.2);
  let best = null;
  for (const [r, c, sz, q] of dets) if (q > 50 && (!best || q > best.q)) best = { r, c, sz, q };
  return best && { x: best.c - best.sz / 2, y: best.r - best.sz / 2, w: best.sz, h: best.sz };
}

function smoothBox(prev, cur, a = 0.15) {
  if (!prev) return { ...cur };
  const out = {};
  for (const k of ["x", "y", "w", "h"]) out[k] = prev[k] + a * (cur[k] - prev[k]);
  return out;
}

function roiRect(box, [fx, fy, fw, fh], W, H) {
  const x = Math.max(0, Math.round(box.x + fx * box.w)), y = Math.max(0, Math.round(box.y + fy * box.h));
  const x2 = Math.min(W, Math.round(box.x + (fx + fw) * box.w)), y2 = Math.min(H, Math.round(box.y + (fy + fh) * box.h));
  return { x, y, w: Math.max(0, x2 - x), h: Math.max(0, y2 - y) };
}

function meanRgb(d, W, r, skinOnly) {
  let R = 0, G = 0, B = 0, c = 0;
  for (let y = r.y; y < r.y + r.h; y++) {
    for (let x = r.x; x < r.x + r.w; x++) {
      const i = (y * W + x) * 4;
      if (skinOnly && !isSkin(d[i], d[i + 1], d[i + 2])) continue;
      R += d[i]; G += d[i + 1]; B += d[i + 2]; c++;
    }
  }
  return c >= 20 ? [R / c, G / c, B / c] : null;
}

// rppg/signals.py TraceExtractor mask_mode="soft": ROI'ye göre sabit 32x32 ızgarada cilt olasılığı
// p ← β·p + (1−β)·m üstel ortalamayla güncellenir, renk p ağırlıklı ortalanır (eşik yok).
// Her karede yeniden hesaplanan ikili maskede eşik sınırındaki pikseller maskeye girip çıkar
// ve bu gürültü nabız sinyalini bastırır (bkz. results/maske_deneyi).
const MASK_GRID = 32, MASK_BETA = 0.98, MIN_SKIN = 0.15;
function meanRgbSoft(d, W, r, name) {
  const G = MASK_GRID, cnt = new Float32Array(G * G), tot = new Float32Array(G * G);
  const cx = new Int32Array(r.w), cy = new Int32Array(r.h);
  for (let x = 0; x < r.w; x++) cx[x] = Math.min(G - 1, Math.floor((x * G) / r.w));
  for (let y = 0; y < r.h; y++) cy[y] = Math.min(G - 1, Math.floor((y * G) / r.h)) * G;
  for (let y = 0; y < r.h; y++) {
    for (let x = 0; x < r.w; x++) {
      const i = ((r.y + y) * W + r.x + x) * 4, k = cy[y] + cx[x];
      tot[k]++;
      if (isSkin(d[i], d[i + 1], d[i + 2])) cnt[k]++;
    }
  }
  let p = state.maskProb[name];
  if (!p) p = state.maskProb[name] = Float32Array.from(cnt, (c, k) => (tot[k] ? c / tot[k] : 0));
  else for (let k = 0; k < p.length; k++) p[k] = MASK_BETA * p[k] + (1 - MASK_BETA) * (tot[k] ? cnt[k] / tot[k] : 0);
  const ratio = p.reduce((a, b) => a + b, 0) / p.length;
  let R = 0, Gs = 0, B = 0, ws = 0;
  for (let y = 0; y < r.h; y++) {
    for (let x = 0; x < r.w; x++) {
      const i = ((r.y + y) * W + r.x + x) * 4, w = ratio >= MIN_SKIN ? p[cy[y] + cx[x]] : 1;
      R += w * d[i]; Gs += w * d[i + 1]; B += w * d[i + 2]; ws += w;
    }
  }
  return ws > 1e-6 ? { rgb: [R / ws, Gs / ws, B / ws], skin: ratio } : null;
}

function grayPatch(d, W, r) {                      // hareket indeksi için seyrek gri örnekler
  const out = [];
  for (let y = r.y; y < r.y + r.h; y += 4) {
    for (let x = r.x; x < r.x + r.w; x += 4) {
      const i = (y * W + x) * 4;
      out.push(0.299 * d[i] + 0.587 * d[i + 1] + 0.114 * d[i + 2]);
    }
  }
  return out;
}

// ------------------------------------------------------------------ kare işleme
function processFrame(tSec) {
  const v = els.video, W = els.work.width, H = els.work.height;
  if (!W || !H) return;
  const ctx = els.work.getContext("2d", { willReadFrequently: true });
  ctx.drawImage(v, 0, 0, W, H);
  const d = ctx.getImageData(0, 0, W, H).data;

  state.frameTimes.push(tSec);
  while (state.frameTimes.length > 30) state.frameTimes.shift();
  let luma = 0, nl = 0;                            // kamera kilidinin görüntüyü karartıp karartmadığını izlemek için
  for (let i = 0; i < d.length; i += 64) { luma += d[i] + d[i + 1] + d[i + 2]; nl++; }
  state.lumaHist.push(luma / (3 * nl));
  while (state.lumaHist.length > 10) state.lumaHist.shift();

  let rgb = null, motion = 0, rois = null;
  const roiRaw = {};
  if (state.mode === "face") {
    if (state.frameNo++ % DETECT_EVERY === 0) {
      const f = detectFace(d, W, H);
      if (f) {
        state.bbox = smoothBox(state.bbox, f, state.bbox ? 0.3 : 1);
        state.lastDet = tSec;
      }
    }
    if (state.bbox && tSec - state.lastDet > 1.5) { state.bbox = null; state.maskProb = {}; }   // yüz 1.5 s görünmedi
    if (state.bbox) {
      rois = {};
      const means = [];
      for (const [name, def] of Object.entries(ROI_DEFS)) {
        rois[name] = roiRect(state.bbox, def, W, H);
        const m = meanRgbSoft(d, W, rois[name], name);
        if (m) { means.push(m.rgb); roiRaw[name] = m; }
      }
      if (means.length) rgb = [0, 1, 2].map((c) => means.reduce((a, m) => a + m[c], 0) / means.length);
      const g = grayPatch(d, W, rois.full);
      if (state.prevGray && state.prevGray.length === g.length) {
        motion = g.reduce((a, v2, i) => a + Math.abs(v2 - state.prevGray[i]), 0) / g.length;
      }
      state.prevGray = g;
      if (state.method === "ai" && !dl.failed) {
        dlCapture(tSec);
        dlSchedule();
      }
    } else {
      state.prevGray = null;
    }
  } else {
    const r = { x: Math.round(W * 0.25), y: Math.round(H * 0.25), w: Math.round(W * 0.5), h: Math.round(H * 0.5) };
    const m = meanRgb(d, W, r, false);
    const covered = m && m[0] > 60 && m[0] > 1.3 * m[1] && m[0] > 1.3 * m[2];
    rgb = covered ? m : null;
    rois = { finger: r };
  }
  state.samples.push({ t: tSec, rgb, motion });
  if (state.raw.length < RAW_MAX) {            // teşhis için ham veri ("Ham veri indir")
    state.raw.push({ t: tSec, mode: state.mode, cam: camName(), rgb, motion, luma: state.lumaHist[state.lumaHist.length - 1],
      face: state.bbox ? Math.round(state.bbox.w) : 0, W,
      rois: Object.fromEntries(Object.entries(roiRaw).map(([k, m]) => [k, [...m.rgb.map((v) => +v.toFixed(3)), +m.skin.toFixed(3)]])) });
  }
  while (state.samples.length && tSec - state.samples[0].t > KEEP_SEC) state.samples.shift();
  drawOverlay(rois);
}

function drawOverlay(rois) {
  const c = els.overlay, box = els.stage.getBoundingClientRect(), dpr = window.devicePixelRatio || 1;
  if (c.width !== Math.round(box.width * dpr)) { c.width = Math.round(box.width * dpr); c.height = Math.round(box.height * dpr); }
  const ctx = c.getContext("2d");
  ctx.clearRect(0, 0, c.width, c.height);
  if (!rois) return;
  // object-fit: contain -> görüntünün kutudaki yeri
  const vw = els.work.width, vh = els.work.height;
  const s = Math.min(c.width / vw, c.height / vh), ox = (c.width - vw * s) / 2, oy = (c.height - vh * s) / 2;
  ctx.lineWidth = 2.5 * dpr;
  if (state.mode === "face" && state.bbox) {
    ctx.strokeStyle = "rgba(255,255,255,.85)";
    ctx.strokeRect(ox + state.bbox.x * s, oy + state.bbox.y * s, state.bbox.w * s, state.bbox.h * s);
  }
  for (const [name, r] of Object.entries(rois)) {
    ctx.strokeStyle = ROI_COLORS[name] || "#ef4444";
    ctx.strokeRect(ox + r.x * s, oy + r.y * s, r.w * s, r.h * s);
  }
}

// ------------------------------------------------------------------ analiz (saniyede bir)
function analyze() {
  const S = state.samples;
  if (S.length < 10) return;
  const tEnd = S[S.length - 1].t;
  const win = S.filter((s) => s.t >= tEnd - WIN_SEC);
  const valid = win.filter((s) => s.rgb);
  const fps = (state.frameTimes.length - 1) / (state.frameTimes[state.frameTimes.length - 1] - state.frameTimes[0] || 1);
  els.fps.textContent = state.mode === "face" && state.method === "ai" && dl.ms ? `${fps.toFixed(0)} fps · YZ ${dl.ms.toFixed(0)} ms` : `${fps.toFixed(0)} fps`;

  const lostMsg = state.mode === "face" ? "Yüz bulunamadı — çerçeveye girin, ışığı artırın" : "Parmağınızı kamera ve flaşın üzerine koyun";
  if (valid.length < win.length * 0.7) {
    setStatus(lostMsg, "bad");
    return;
  }
  const span = valid.length ? valid[valid.length - 1].t - valid[0].t : 0;
  if (span < MIN_SEC) {
    els.progressWrap.hidden = false;
    els.progress.style.width = `${Math.min(100, (100 * span) / MIN_SEC)}%`;
    const lock = !state.camLock ? "" : state.camLock === "yok"
      ? " · kamera ayarı kilitlenemedi, ışığı sabit tutun" : ` · kilitli: ${state.camLock}`;
    setStatus(`Ölçülüyor… ${Math.ceil(MIN_SEC - span)} s${lock}`, "fair");
    return;
  }
  els.progressWrap.hidden = true;

  const t = valid.map((s) => s.t), rgb = valid.map((s) => s.rgb);
  let res;
  if (state.mode === "face" && state.method === "ai" && !dl.failed) {
    const ser = dlSeries(WIN_SEC), dspan = ser ? ser.t[ser.t.length - 1] - ser.t[0] : 0;
    if (dspan < MIN_SEC) {                         // model dalgası henüz 8 s'ye ulaşmadı
      els.progressWrap.hidden = false;
      els.progress.style.width = `${Math.min(100, (100 * dspan) / MIN_SEC)}%`;
      setStatus(dl.ready ? "Yapay zekâ ölçüyor…" : "Yapay zekâ modeli yükleniyor…", "fair");
      return;
    }
    const bvp = preprocessBvp(ser.x);
    res = { bvp, spec: spectrumBpm(bvp) };
  } else if (state.mode === "face") {
    res = analyzeWindow(t, rgb, { method: "pos" });
  } else {                                          // parmak: G ve R kanalından SNR'si yüksek olan
    const cands = [1, 0].map((ch) => analyzeWindow(t, rgb, { method: "channel", channel: ch }));
    const snrOf = (r) => windowSnr(BPM_GRID, r.spec, BPM_GRID[r.spec.indexOf(Math.max(...r.spec))]);
    res = snrOf(cands[0]) >= snrOf(cands[1]) ? cands[0] : cands[1];
  }

  const m = valid.reduce((a, s) => a + s.motion, 0) / valid.length;
  const conf = state.mode === "face" ? motionConfidence(m, state.motionHist) : 1;
  state.motionHist.push(m);
  if (state.motionHist.length > 60) state.motionHist.shift();

  const hr = state.tracker.update(res.spec, 1, conf);
  const snr = windowSnr(BPM_GRID, res.spec, hr);
  const level = snr > 3 ? "good" : snr > -1 ? "fair" : "bad";
  const label = { good: "Sinyal iyi", fair: "Sinyal orta — hareketsiz kalın", bad: "Sinyal zayıf — ışığı artırın, kıpırdamayın" }[level];

  els.hr.textContent = hr.toFixed(0);
  els.snr.textContent = `${snr.toFixed(1)} dB`;
  els.conf.textContent = state.mode === "face" ? conf.toFixed(2) : "—";
  const fallback = state.mode === "face" && state.method === "ai" && dl.failed ? " · model çalışmadı, klasik yöntem" : "";
  setStatus((conf < 0.4 ? "Hareket algılandı — sabit durun" : label) + fallback, conf < 0.4 ? "fair" : level);

  state.log.push({ t: tEnd - state.t0, hr, snr, conf, mode: state.mode, method: methodName(), cam: camName(), lock: state.camLock || "-" });
  state.lastBvp = res.bvp;
  els.csv.disabled = els.raw.disabled = false;
  els.reset.disabled = false;
  drawLine(els.plotBvp, res.bvp.slice(-150), { color: "#60a5fa" });
  drawSpectrum(els.plotSpec, res.spec, hr);
  drawLine(els.plotHist, state.log.map((r) => r.hr), { color: "#ef4444", range: [40, 180], labels: true });
}

// ------------------------------------------------------------------ çizim
function fitCanvas(c) {
  const dpr = window.devicePixelRatio || 1, r = c.getBoundingClientRect();
  if (c.width !== Math.round(r.width * dpr)) { c.width = Math.round(r.width * dpr); c.height = Math.round(r.height * dpr); }
  const ctx = c.getContext("2d");
  ctx.clearRect(0, 0, c.width, c.height);
  return { ctx, w: c.width, h: c.height, dpr };
}

function drawLine(c, y, { color, range, labels } = {}) {
  const { ctx, w, h, dpr } = fitCanvas(c);
  if (y.length < 2) return;
  let lo = range ? range[0] : Math.min(...y), hi = range ? range[1] : Math.max(...y);
  if (range) { lo = Math.min(lo, ...y); hi = Math.max(hi, ...y); }
  const pad = 6 * dpr, sy = (v) => h - pad - ((v - lo) / (hi - lo || 1)) * (h - 2 * pad);
  if (labels) {
    ctx.fillStyle = "#8b93a5";
    ctx.font = `${10 * dpr}px system-ui`;
    ctx.fillText(`${hi.toFixed(0)}`, 2 * dpr, 11 * dpr);
    ctx.fillText(`${lo.toFixed(0)}`, 2 * dpr, h - 3 * dpr);
  }
  ctx.strokeStyle = color;
  ctx.lineWidth = 2 * dpr;
  ctx.beginPath();
  y.forEach((v, i) => {
    const x = (i / (y.length - 1)) * w;
    i ? ctx.lineTo(x, sy(v)) : ctx.moveTo(x, sy(v));
  });
  ctx.stroke();
}

function drawSpectrum(c, p, hr) {
  const { ctx, w, h, dpr } = fitCanvas(c);
  const mx = Math.max(...p), g0 = BPM_GRID[0], g1 = BPM_GRID[BPM_GRID.length - 1];
  const sx = (bpm) => ((bpm - g0) / (g1 - g0)) * w;
  ctx.fillStyle = "#8b93a5";
  ctx.font = `${10 * dpr}px system-ui`;
  for (const b of [60, 90, 120, 150, 180]) ctx.fillText(`${b}`, sx(b) - 8 * dpr, h - 2 * dpr);
  ctx.strokeStyle = "#f97316";
  ctx.lineWidth = 2 * dpr;
  ctx.beginPath();
  p.forEach((v, i) => {
    const x = sx(BPM_GRID[i]), y = h - 14 * dpr - (v / mx) * (h - 20 * dpr);
    i ? ctx.lineTo(x, y) : ctx.moveTo(x, y);
  });
  ctx.stroke();
  ctx.strokeStyle = "rgba(255,255,255,.6)";
  ctx.lineWidth = 1 * dpr;
  ctx.beginPath();
  ctx.moveTo(sx(hr), 0);
  ctx.lineTo(sx(hr), h - 14 * dpr);
  ctx.stroke();
}

// ------------------------------------------------------------------ yapay zekâ (derin öğrenme) hattı
// Eğitimdeki ön işlemeyle aynı: yüz kutusu merkez sabit x1.5 büyütülür, 72x72'ye küçültülür (ham RGB, 0–255),
// kareler zaman damgalarına göre 30 fps'lik sabit ızgaraya doğrusal enterpole edilir. Model 161 karelik
// pencereden 160 örneklik nabız dalgası verir; pencereler yarı örtüşür (80 kare ≈ 2.7 s'de bir) ve Hann
// ağırlıklarıyla birleştirilir. Sonuç klasik hattaki gibi detrend + bant geçiren + spektrum + takipten geçer.
const DL_SIZE = 72, DL_T = 160, DL_HOP = 80, DL_FS = 30, DL_BOX = 1.5, DL_KEEP_SEC = 12, DL_MAX_GAP = 0.35;
const dl = { worker: null, ready: false, failed: "", busy: false, gen: 0, frames: [], t0: null, nextK: null,
  acc: new Map(), ms: 0, canvas: null };
window.__rppgDl = dl; // tarayıcı testleri için

function dlInit() {
  if (dl.worker || dl.failed) return;
  try {
    dl.worker = new Worker("dl_worker.js", { type: "module" });
  } catch (e) {
    dl.failed = "bu tarayıcı modeli çalıştıramıyor";
    return;
  }
  dl.worker.onmessage = (e) => {
    const m = e.data;
    if (m.type === "ready") dl.ready = true;
    else if (m.type === "error") { dl.failed = m.message; dl.busy = false; }
    else if (m.type === "bvp") {
      dl.busy = false;
      dl.ms = m.ms;
      if (m.gen === dl.gen) dlAddBvp(m.k0, m.bvp);
      dlSchedule();
    }
  };
  dl.worker.onerror = (e) => { dl.failed = e.message || "model yüklenemedi"; dl.busy = false; };
  dl.worker.postMessage({ type: "load" });
}

function dlReset() {
  dl.gen++;
  dl.frames = [];
  dl.t0 = null;
  dl.nextK = null;
  dl.acc.clear();
}

function dlCapture(tSec) {                     // yüz kutusundan 72x72 RGB kırpıntı (tam çözünürlüklü kareden)
  const v = els.video, b = state.bbox, vw = v.videoWidth, vh = v.videoHeight, sc = vw / els.work.width;
  if (!dl.canvas) {
    dl.canvas = document.createElement("canvas");
    dl.canvas.width = dl.canvas.height = DL_SIZE;
  }
  const size = Math.max(b.w, b.h) * DL_BOX * sc, cx = (b.x + b.w / 2) * sc, cy = (b.y + b.h / 2) * sc;
  const x0 = Math.max(0, cx - size / 2), y0 = Math.max(0, cy - size / 2);
  const x1 = Math.min(vw, cx + size / 2), y1 = Math.min(vh, cy + size / 2);
  if (x1 - x0 < 8 || y1 - y0 < 8) return;
  const ctx = dl.canvas.getContext("2d", { willReadFrequently: true });
  ctx.imageSmoothingEnabled = true;
  ctx.imageSmoothingQuality = "high";            // alan ortalamasına yakın küçültme (eğitimde INTER_AREA)
  ctx.drawImage(v, x0, y0, x1 - x0, y1 - y0, 0, 0, DL_SIZE, DL_SIZE);
  const d = ctx.getImageData(0, 0, DL_SIZE, DL_SIZE).data, px = new Uint8Array(DL_SIZE * DL_SIZE * 3);
  for (let i = 0, j = 0; j < px.length; i += 4, j += 3) { px[j] = d[i]; px[j + 1] = d[i + 1]; px[j + 2] = d[i + 2]; }
  dl.frames.push({ t: tSec, px });
  if (dl.t0 === null) dl.t0 = tSec;
  while (dl.frames.length && tSec - dl.frames[0].t > DL_KEEP_SEC) dl.frames.shift();
}

function dlSchedule() {
  if (!dl.ready || dl.busy || dl.frames.length < 2 || dl.t0 === null) return;
  const F = dl.frames, kLast = Math.floor((F[F.length - 1].t - dl.t0) * DL_FS);
  if (dl.nextK === null) dl.nextK = Math.max(DL_T, Math.ceil((F[0].t - dl.t0) * DL_FS) + DL_T);
  if (kLast < dl.nextK) return;
  const kEnd = kLast - dl.nextK > DL_HOP ? kLast : dl.nextK;   // geride kaldıysa en yeniye atla
  const k0 = kEnd - DL_T, T = DL_T + 1, P = DL_SIZE * DL_SIZE;
  dl.nextK = kEnd + DL_HOP;
  if (dl.t0 + k0 / DL_FS < F[0].t) return;                   // pencerenin başı artık bellekte yok
  const out = new Float32Array(3 * T * P);
  let j = 0;
  for (let i = 0; i < T; i++) {
    const t = dl.t0 + (k0 + i) / DL_FS;
    while (j < F.length - 2 && F[j + 1].t <= t) j++;
    const a = F[j], b = F[j + 1];
    if (b.t - a.t > DL_MAX_GAP) return;                       // yüz kayboldu / kare atlandı: bu pencereyi geç
    const w = Math.min(1, Math.max(0, (t - a.t) / (b.t - a.t || 1)));
    for (let p = 0, q = 0; p < P; p++, q += 3) {
      for (let c = 0; c < 3; c++) out[c * T * P + i * P + p] = a.px[q + c] * (1 - w) + b.px[q + c] * w;
    }
  }
  dl.busy = true;
  dl.worker.postMessage({ type: "run", frames: out, T, k0, gen: dl.gen }, [out.buffer]);
}

function dlAddBvp(k0, bvp) {
  let m = 0, s = 0;
  for (const v of bvp) m += v;
  m /= bvp.length;
  for (const v of bvp) s += (v - m) ** 2;
  s = Math.sqrt(s / bvp.length) || 1;
  for (let i = 0; i < bvp.length; i++) {
    const w = Math.sin((Math.PI * (i + 0.5)) / bvp.length) ** 2, k = k0 + i, e = dl.acc.get(k) || [0, 0];
    e[0] += (w * (bvp[i] - m)) / s;
    e[1] += w;
    dl.acc.set(k, e);
  }
  const kMin = k0 + bvp.length - 20 * DL_FS;
  for (const k of dl.acc.keys()) if (k < kMin) dl.acc.delete(k);
}

function dlSeries(winSec) {                    // son winSec saniyenin birleşik nabız dalgası (30 Hz)
  if (!dl.acc.size) return null;
  const ks = [...dl.acc.keys()].sort((a, b) => a - b), kMax = ks[ks.length - 1];
  const t = [], x = [];
  for (const k of ks) {
    if (k <= kMax - winSec * DL_FS) continue;
    const [v, w] = dl.acc.get(k);
    if (w < 0.1) continue;                      // pencere kenarındaki çok düşük ağırlıklı örnekler
    t.push(dl.t0 + k / DL_FS);
    x.push(v / w);
  }
  return x.length ? { t, x } : null;
}

// ------------------------------------------------------------------ kamera
// Otomatik pozlama / beyaz dengesi / odak, karelerin parlaklığını ve rengini nabız
// sinyalinden (~%0.5) çok daha büyük oranda sürekli değiştirir (bkz. rppg/camera.py).
// Destekleyen tarayıcıda (Android Chrome) o anki değerlerinde sabitlenir.
// Kilitten sonra parlaklık belirgin değişirse ayar otomatiğe geri alınır.
const meanLuma = () => state.lumaHist.reduce((a, b) => a + b, 0) / (state.lumaHist.length || 1);
const wait = (ms) => new Promise((r) => setTimeout(r, ms));

async function lockCamera(track) {
  const caps = track.getCapabilities?.() || {}, cur = track.getSettings?.() || {};
  const want = [
    ["whiteBalanceMode", { whiteBalanceMode: "manual", ...(cur.colorTemperature ? { colorTemperature: cur.colorTemperature } : {}) }],
    ["focusMode", { focusMode: "manual", ...(cur.focusDistance ? { focusDistance: cur.focusDistance } : {}) }],
  ];
  // Pozlama kilitlenmez: telefonlarda manuel pozlama görüntüyü karartıyor ve otomatiğe dönüş
  // her cihazda çalışmıyor (sahada görüldü). Pozlama değişimlerine karşı ışık sabit tutulmalı.
  const locked = [];
  for (const [key, c] of want) {
    if (!caps[key]?.includes?.("manual")) continue;
    const before = meanLuma();
    try {
      await track.applyConstraints({ advanced: [c] });
      if (track.getSettings?.()[key] !== "manual") continue;
      await wait(700);
      const ratio = meanLuma() / (before || 1);
      if (ratio < 0.8 || ratio > 1.25) {           // görüntü karardı / patladı: geri al
        await track.applyConstraints({ advanced: [{ [key]: "continuous" }] }).catch(() => {});
        continue;
      }
      locked.push(key);
    } catch { /* bu ayar desteklenmiyor */ }
  }
  const names = { exposureMode: "pozlama", whiteBalanceMode: "beyaz dengesi", focusMode: "odak" };
  return locked.length ? locked.map((k) => names[k]).join(", ") : "yok";
}

async function start() {
  if (!navigator.mediaDevices?.getUserMedia) {
    setStatus("Bu tarayıcı kameraya erişemiyor (HTTPS gerekli)", "bad");
    return;
  }
  const facingMode = state.mode === "face" ? state.facing : "environment";
  try {
    state.stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode, width: { ideal: 640 }, height: { ideal: 480 }, frameRate: { ideal: 30 } },
      audio: false,
    });
  } catch (e) {
    setStatus(`Kamera açılamadı: ${e.name === "NotAllowedError" ? "izin verilmedi" : e.message}`, "bad");
    return;
  }
  state.track = state.stream.getVideoTracks()[0];
  els.video.srcObject = state.stream;
  await els.video.play().catch(() => {});
  await new Promise((r) => (els.video.videoWidth ? r() : els.video.addEventListener("loadedmetadata", r, { once: true })));

  const vw = els.video.videoWidth, vh = els.video.videoHeight, s = WORK_MAX / Math.max(vw, vh);
  els.work.width = Math.round(vw * s);
  els.work.height = Math.round(vh * s);
  els.stage.style.aspectRatio = `${vw} / ${vh}`;

  state.torch = false;
  if (state.mode === "finger") {
    try {
      const caps = state.track.getCapabilities?.() || {};
      if (caps.torch) {
        await state.track.applyConstraints({ advanced: [{ torch: true }] });
        state.torch = true;
      }
    } catch { /* flaş desteklenmiyor */ }
  }

  if (state.mode === "face") {
    if (state.method === "ai") dlInit();
    try {
      await loadFaceDetector();
    } catch {
      setStatus("Yüz dedektörü yüklenemedi — internet bağlantısını kontrol edin", "bad");
      stop();
      return;
    }
  }
  resetMeasurement();
  state.camLock = "";
  state.lumaHist = [];
  state.raw = [];
  navigator.wakeLock?.request("screen").then((w) => (state.wakeLock = w)).catch(() => {});   // ekran kararmasın
  const track = state.track;
  setTimeout(async () => {          // pozlama önce sahneye otursun, sonra kilitle ve baştan ölç
    if (!state.running || state.track !== track) return;
    state.camLock = await lockCamera(track);
    if (state.running && state.track === track) resetMeasurement();
  }, LOCK_AFTER_MS);
  state.running = true;
  state.t0 = null;
  state.clock = null;
  els.placeholder.hidden = true;
  els.stage.classList.add("running");
  els.start.textContent = "Durdur";
  els.start.classList.add("stop");
  setStatus(state.mode === "finger" && !state.torch ? "Flaş açılamadı — aydınlık ortamda deneyin" : "Başlıyor…", "fair");

  const onFrame = (now, meta) => {
    if (!state.running) return;
    // tek bir saat kullan: varsa karenin kendi zamanı (mediaTime), yoksa çağrı zamanı
    if (state.clock === null) state.clock = meta?.mediaTime > 0 ? "media" : "now";
    const t = state.clock === "media" ? meta.mediaTime : now / 1000;
    if (state.t0 === null) state.t0 = t;
    processFrame(t);
    schedule();
  };
  const schedule = () => {
    if (els.video.requestVideoFrameCallback) els.video.requestVideoFrameCallback(onFrame);
    else requestAnimationFrame((now) => onFrame(now));
  };
  schedule();
  state.timer = setInterval(analyze, 1000);
}

function stop() {
  state.running = false;
  state.wakeLock?.release().catch(() => {});
  state.wakeLock = null;
  els.raw.disabled = !state.raw.length;
  clearInterval(state.timer);
  state.stream?.getTracks().forEach((t) => t.stop());
  state.stream = null;
  els.video.srcObject = null;
  els.placeholder.hidden = false;
  els.stage.classList.remove("running");
  els.start.textContent = "Ölçümü başlat";
  els.start.classList.remove("stop");
  els.progressWrap.hidden = true;
  drawOverlay(null);
  setStatus(state.log.length ? `Durduruldu — ortalama ${avgHr().toFixed(0)} BPM` : "Hazır");
}

function resetMeasurement() {
  dlReset();
  state.samples = [];
  state.maskProb = {};
  state.tracker.reset();
  state.motionHist = [];
  state.bbox = null;
  state.lastDet = 0;
  state.frameNo = 0;
  state.prevGray = null;
  state.frameTimes = [];
  els.hr.textContent = "--";
  els.snr.textContent = els.conf.textContent = "--";
}

function avgHr() {
  const last = state.log.slice(-20);
  return last.reduce((a, r) => a + r.hr, 0) / (last.length || 1);
}

function setMode(mode) {
  if (mode === state.mode) return;
  const wasRunning = state.running;
  if (wasRunning) stop();
  state.mode = mode;
  els.modeFace.classList.toggle("on", mode === "face");
  els.modeFinger.classList.toggle("on", mode === "finger");
  els.modeFace.setAttribute("aria-selected", mode === "face");
  els.modeFinger.setAttribute("aria-selected", mode === "finger");
  applyFacing();
  els.method.hidden = mode !== "face";
  els.stage.classList.toggle("finger", mode === "finger");
  els.placeholderText.textContent = mode === "face"
    ? "Yüzünüzü çerçeveye alın, iyi aydınlatılmış bir yerde hareketsiz durun."
    : "Parmak ucunuzu arka kamerayı ve flaşı kapatacak şekilde hafifçe koyun.";
  if (wasRunning) start();
}

// Görüntü yalnızca ön kamerada aynalanır (ayna gibi doğal görünsün); arka kamerada gerçek yön.
function applyFacing() {
  els.stage.classList.toggle("mirror", state.mode === "face" && state.facing === "user");
  els.flipLabel.textContent = state.facing === "user" ? "Ön kamera" : "Arka kamera";
  els.flip.setAttribute("aria-label", `Kamerayı değiştir (şu an ${els.flipLabel.textContent.toLowerCase()})`);
}

function applyMethod() {
  els.methodAi.classList.toggle("on", state.method === "ai");
  els.methodPos.classList.toggle("on", state.method === "pos");
  els.methodAi.setAttribute("aria-selected", state.method === "ai");
  els.methodPos.setAttribute("aria-selected", state.method === "pos");
}

function setMethod(m) {
  if (m === state.method) return;
  state.method = m;
  try { localStorage.setItem(METHOD_KEY, m); } catch { /* gizli sekme vb. */ }
  applyMethod();
  if (state.running) {               // aynı kamera akışıyla baştan ölç
    if (m === "ai") dlInit();
    resetMeasurement();
  }
}

async function flipCamera() {
  state.facing = state.facing === "user" ? "environment" : "user";
  try { localStorage.setItem(FACING_KEY, state.facing); } catch { /* gizli sekme vb. */ }
  applyFacing();
  if (state.running) {               // ölçüm sürüyorsa yeni kamerayla baştan başlar
    els.flip.disabled = true;
    stop();
    await start();
    els.flip.disabled = false;
  }
}

function saveFile(name, text, type) {
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([text], { type }));
  a.download = name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 1000);
}

const stamp = () => new Date().toISOString().slice(0, 19).replace(/[:T]/g, "-");

// Teşhis: kare başına ham renk ortalamaları, zaman damgaları, yüz boyutu, cilt oranı, kamera kilidi
function downloadRaw() {
  const meta = { ua: navigator.userAgent, method: methodName(), dl_ms: dl.ms, dl_error: dl.failed, facing: camName(), camera: state.track?.getSettings?.() || {}, lock: state.camLock,
    work: [els.work.width, els.work.height], log: state.log };
  saveFile(`rppg_ham_${stamp()}.json`, JSON.stringify({ meta, frames: state.raw }), "application/json");
}

function downloadCsv() {
  const rows = ["zaman_s,nabiz_bpm,snr_db,hareket_guveni,mod,yontem,kamera,kamera_kilidi",
    ...state.log.map((r) => [r.t.toFixed(1), r.hr.toFixed(2), r.snr.toFixed(2), r.conf.toFixed(2), r.mode,
      `"${r.method || ""}"`, r.cam || "", `"${r.lock}"`].join(","))];
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([rows.join("\n")], { type: "text/csv" }));
  a.download = `rppg_oturum_${new Date().toISOString().slice(0, 19).replace(/[:T]/g, "-")}.csv`;
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 1000);
}

// ------------------------------------------------------------------ olaylar
els.start.addEventListener("click", () => (state.running ? stop() : start()));
els.modeFace.addEventListener("click", () => setMode("face"));
els.modeFinger.addEventListener("click", () => setMode("finger"));
els.flip.addEventListener("click", flipCamera);
els.methodAi.addEventListener("click", () => setMethod("ai"));
els.methodPos.addEventListener("click", () => setMethod("pos"));
els.csv.addEventListener("click", downloadCsv);
els.raw.addEventListener("click", downloadRaw);
els.reset.addEventListener("click", () => {
  state.log = [];
  resetMeasurement();
  [els.plotBvp, els.plotSpec, els.plotHist].forEach((c) => fitCanvas(c));
  state.raw = [];
  els.csv.disabled = els.raw.disabled = els.reset.disabled = true;
});
document.addEventListener("visibilitychange", () => { if (document.hidden && state.running) stop(); });
applyFacing();
applyMethod();

if ("serviceWorker" in navigator && !params.has("autotest")) {
  navigator.serviceWorker.register("sw.js").catch(() => {});
}
if (params.get("autotest") === "finger") setMode("finger");
if (params.has("autotest")) start();
