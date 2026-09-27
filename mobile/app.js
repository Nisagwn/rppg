// rPPG Nabız — telefon uygulaması.
// Yüz modu:   ön kamera -> pico yüz tespiti (Markuš vd. 2013; piksel karşılaştırmalı karar ağaçları,
//             Viola–Jones ailesinden klasik yöntem) -> 4 ROI (alın, yanaklar, tüm yüz) + YCrCb cilt maskesi
//             -> cilt piksellerinin RGB ortalaması -> POS -> detrend + bant geçiren -> spektrum
//             -> hareket güvenli çevrimiçi Bayes takibi (Viterbi'nin çevrimiçi eşi).
//             ROI'ler ortalama füzyonla birleşir: gerçek veride (UBFC, MCD-rPPG) en iyi sonucu veren hat.
// Parmak modu: arka kamera + flaş, merkez bölgenin G/R kanalı (temaslı PPG).
import {
  BPM_GRID, OnlineHRTracker, analyzeWindow, motionConfidence, windowSnr,
} from "./dsp.js";

const ROI_DEFS = {               // rppg/roi.py ROI_DEFS ile aynı (yüz kutusuna göre kesirler)
  forehead: [0.30, 0.08, 0.40, 0.17],
  left_cheek: [0.15, 0.50, 0.22, 0.22],
  right_cheek: [0.63, 0.50, 0.22, 0.22],
  full: [0.20, 0.10, 0.60, 0.80],
};
const ROI_COLORS = { forehead: "#3b82f6", left_cheek: "#f97316", right_cheek: "#22c55e", full: "#a855f7" };
const WIN_SEC = 10, MIN_SEC = 8, KEEP_SEC = 20, WORK_MAX = 480, DETECT_EVERY = 4, LOCK_AFTER_MS = 2000;
/* global pico */

const $ = (id) => document.getElementById(id);
const els = {
  stage: $("stage"), video: $("video"), overlay: $("overlay"), work: $("work"),
  placeholder: $("placeholder"), placeholderText: $("placeholder-text"),
  hr: $("hr"), snr: $("snr"), conf: $("conf"), fps: $("fps"), status: $("status"),
  progressWrap: $("progress-wrap"), progress: $("progress"),
  start: $("start"), csv: $("csv"), reset: $("reset"),
  modeFace: $("mode-face"), modeFinger: $("mode-finger"),
  plotBvp: $("plot-bvp"), plotSpec: $("plot-spec"), plotHist: $("plot-hist"),
};
const params = new URLSearchParams(location.search);

const state = {
  mode: "face", running: false, stream: null, track: null, torch: false, camLock: "",
  samples: [], tracker: new OnlineHRTracker(), motionHist: [],
  bbox: null, lastDet: 0, frameNo: 0, prevGray: null, frameTimes: [], log: [], t0: 0, timer: null, lastBvp: null,
};
window.__rppg = state; // tarayıcı testleri ve hata ayıklama için

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

  let rgb = null, motion = 0, rois = null;
  if (state.mode === "face") {
    if (state.frameNo++ % DETECT_EVERY === 0) {
      const f = detectFace(d, W, H);
      if (f) {
        state.bbox = smoothBox(state.bbox, f, state.bbox ? 0.3 : 1);
        state.lastDet = tSec;
      }
    }
    if (state.bbox && tSec - state.lastDet > 1.5) state.bbox = null;   // yüz 1.5 s görünmedi
    if (state.bbox) {
      rois = {};
      const means = [];
      for (const [name, def] of Object.entries(ROI_DEFS)) {
        rois[name] = roiRect(state.bbox, def, W, H);
        const m = meanRgb(d, W, rois[name], true);
        if (m) means.push(m);
      }
      if (means.length) rgb = [0, 1, 2].map((c) => means.reduce((a, m) => a + m[c], 0) / means.length);
      const g = grayPatch(d, W, rois.full);
      if (state.prevGray && state.prevGray.length === g.length) {
        motion = g.reduce((a, v2, i) => a + Math.abs(v2 - state.prevGray[i]), 0) / g.length;
      }
      state.prevGray = g;
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
  els.fps.textContent = `${fps.toFixed(0)} fps`;

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
  if (state.mode === "face") {
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
  setStatus(conf < 0.4 ? "Hareket algılandı — sabit durun" : label, conf < 0.4 ? "fair" : level);

  state.log.push({ t: tEnd - state.t0, hr, snr, conf, mode: state.mode, lock: state.camLock || "-" });
  state.lastBvp = res.bvp;
  els.csv.disabled = false;
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

// ------------------------------------------------------------------ kamera
// Otomatik pozlama / beyaz dengesi / odak, karelerin parlaklığını ve rengini nabız
// sinyalinden (~%0.5) çok daha büyük oranda sürekli değiştirir (bkz. rppg/camera.py).
// Destekleyen tarayıcıda (Android Chrome) o anki değerlerinde sabitlenir.
async function lockCamera(track) {
  const caps = track.getCapabilities?.() || {}, cur = track.getSettings?.() || {};
  const want = [
    ["exposureMode", { exposureMode: "manual", ...(cur.exposureTime ? { exposureTime: cur.exposureTime } : {}),
      ...(cur.iso ? { iso: cur.iso } : {}) }],
    ["whiteBalanceMode", { whiteBalanceMode: "manual", ...(cur.colorTemperature ? { colorTemperature: cur.colorTemperature } : {}) }],
    ["focusMode", { focusMode: "manual", ...(cur.focusDistance ? { focusDistance: cur.focusDistance } : {}) }],
  ];
  const locked = [];
  for (const [key, c] of want) {
    if (!caps[key]?.includes?.("manual")) continue;
    try {
      await track.applyConstraints({ advanced: [c] });
      if (track.getSettings?.()[key] === "manual") locked.push(key);
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
  const facingMode = state.mode === "face" ? "user" : "environment";
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
  state.samples = [];
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
  els.stage.classList.toggle("mirror", mode === "face");
  els.stage.classList.toggle("finger", mode === "finger");
  els.placeholderText.textContent = mode === "face"
    ? "Yüzünüzü çerçeveye alın, iyi aydınlatılmış bir yerde hareketsiz durun."
    : "Parmak ucunuzu arka kamerayı ve flaşı kapatacak şekilde hafifçe koyun.";
  if (wasRunning) start();
}

function downloadCsv() {
  const rows = ["zaman_s,nabiz_bpm,snr_db,hareket_guveni,mod,kamera_kilidi",
    ...state.log.map((r) => [r.t.toFixed(1), r.hr.toFixed(2), r.snr.toFixed(2), r.conf.toFixed(2), r.mode,
      `"${r.lock}"`].join(","))];
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
els.csv.addEventListener("click", downloadCsv);
els.reset.addEventListener("click", () => {
  state.log = [];
  resetMeasurement();
  [els.plotBvp, els.plotSpec, els.plotHist].forEach((c) => fitCanvas(c));
  els.csv.disabled = els.reset.disabled = true;
});
document.addEventListener("visibilitychange", () => { if (document.hidden && state.running) stop(); });
els.stage.classList.add("mirror");

if ("serviceWorker" in navigator && !params.has("autotest")) {
  navigator.serviceWorker.register("sw.js").catch(() => {});
}
if (params.get("autotest") === "finger") setMode("finger");
if (params.has("autotest")) start();
