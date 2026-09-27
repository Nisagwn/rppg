// rPPG sinyal işleme — rppg/ Python paketinin tarayıcı (ve Node) karşılığı.
// Her fonksiyonun yanında karşılık geldiği Python fonksiyonu yazılıdır.
// Örnekleme hızı sabit FS = 30 Hz'e yeniden örneklenerek çalışılır (filtre katsayıları buna göre).

export const FS = 30;

// rppg.hr.BPM_GRID: 42–210 BPM, 0.5 adım
export const BPM_GRID = Array.from({ length: 337 }, (_, i) => 42 + 0.5 * i);

// scipy.signal.butter(3, [0.7, 3.5], "bandpass", fs=30, output="sos")
const SOS_HR = [
  [0.0151743109298077, 0.0303486218596154, 0.0151743109298077, 1.0, -1.45196150792469, 0.536195295459033],
  [1.0, 0.0, -1.0, 1.0, -1.2486587514639, 0.631245026009257],
  [1.0, -2.0, 1.0, 1.0, -1.87493731108198, 0.897502386514392],
];

const mean = (x) => x.reduce((a, b) => a + b, 0) / x.length;
const std = (x) => {
  const m = mean(x);
  return Math.sqrt(x.reduce((a, b) => a + (b - m) ** 2, 0) / x.length);
};

// rppg.filtering.resample_uniform — düzensiz zaman damgalı örnekler -> sabit fs
export function resampleUniform(t, rows, fs = FS) {
  const t0 = t[0], T = t[t.length - 1] - t0;
  const n = Math.floor(T * fs);
  const out = new Array(n);
  let j = 0;
  for (let i = 0; i < n; i++) {
    const tt = t0 + i / fs;
    while (j < t.length - 2 && t[j + 1] < tt) j++;
    const a = rows[j], b = rows[j + 1], dt = t[j + 1] - t[j];
    const w = dt > 0 ? Math.min(1, Math.max(0, (tt - t[j]) / dt)) : 0;
    out[i] = Array.isArray(a) ? a.map((v, k) => v + w * (b[k] - v)) : a + w * (b - a);
  }
  return out;
}

// rppg.methods.pos — Wang vd. 2017, 1.6 s pencereli örtüşmeli toplama (_overlap_add)
export function pos(rgb, fs = FS, winSec = 1.6) {
  const n = rgb.length;
  const L = Math.max(8, Math.ceil(winSec * fs));
  const f = (seg) => {
    const m = [0, 1, 2].map((c) => mean(seg.map((p) => p[c])) || 1e-6);
    const s1 = seg.map((p) => p[1] / m[1] - p[2] / m[2]);
    const s2 = seg.map((p) => -2 * p[0] / m[0] + p[1] / m[1] + p[2] / m[2]);
    const a = std(s1) / (std(s2) + 1e-12);
    return s1.map((v, i) => v + a * s2[i]);
  };
  if (n <= L) return f(rgb);
  const out = new Float64Array(n), wsum = new Float64Array(n);
  const hann = Array.from({ length: L }, (_, i) => 0.5 - 0.5 * Math.cos((2 * Math.PI * i) / (L - 1)));
  const step = Math.max(1, Math.floor(L / 2));
  const starts = [];
  for (let s = 0; s <= n - L; s += step) starts.push(s);
  if (starts[starts.length - 1] !== n - L) starts.push(n - L);
  for (const s of starts) {
    let h = f(rgb.slice(s, s + L));
    const hm = mean(h);
    h = h.map((v) => v - hm);
    const sd = std(h);
    if (sd > 1e-12) h = h.map((v) => v / sd);
    for (let i = 0; i < L; i++) {
      out[s + i] += h[i] * hann[i];
      wsum[s + i] += hann[i];
    }
  }
  return Array.from(out, (v, i) => v / (wsum[i] || 1));
}

// rppg.filtering.detrend_tarvainen — (I + λ² D2ᵀD2) z_trend = x, beşli bant sistem Cholesky ile
export function detrendTarvainen(x, lam = 100) {
  const n = x.length;
  if (n < 4) {
    const m = mean(x);
    return x.map((v) => v - m);
  }
  const l2 = lam * lam;
  // A = I + l2*D2ᵀD2 simetrik, bant genişliği 2: köşegenler d0, d1, d2
  const d0 = new Float64Array(n), d1 = new Float64Array(n - 1), d2 = new Float64Array(n - 2);
  for (let k = 0; k < n - 2; k++) {
    const c = [1, -2, 1];
    for (let a = 0; a < 3; a++) {
      d0[k + a] += l2 * c[a] * c[a];
      if (a < 2) d1[k + a] += l2 * c[a] * c[a + 1];
    }
    d2[k] += l2 * c[0] * c[2];
  }
  for (let i = 0; i < n; i++) d0[i] += 1;
  // bant Cholesky: A = L Lᵀ,  L köşegenleri l0, l1, l2
  const l0 = new Float64Array(n), l1 = new Float64Array(n), l2v = new Float64Array(n);
  for (let i = 0; i < n; i++) {
    if (i >= 2) l2v[i] = d2[i - 2] / l0[i - 2];
    if (i >= 1) l1[i] = (d1[i - 1] - (i >= 2 ? l2v[i] * l1[i - 1] : 0)) / l0[i - 1];
    l0[i] = Math.sqrt(d0[i] - l1[i] ** 2 - l2v[i] ** 2);
  }
  const y = new Float64Array(n);
  for (let i = 0; i < n; i++) {
    y[i] = (x[i] - (i >= 1 ? l1[i] * y[i - 1] : 0) - (i >= 2 ? l2v[i] * y[i - 2] : 0)) / l0[i];
  }
  const z = new Float64Array(n);
  for (let i = n - 1; i >= 0; i--) {
    z[i] = (y[i] - (i + 1 < n ? l1[i + 1] * z[i + 1] : 0) - (i + 2 < n ? l2v[i + 2] * z[i + 2] : 0)) / l0[i];
  }
  return x.map((v, i) => v - z[i]);
}

// scipy.signal.sosfilt_zi
function sosfiltZi(sos) {
  let scale = 1;
  return sos.map(([b0, b1, b2, , a1, a2]) => {
    // lfilter_zi: (I - Aᵀ) zi = b[1:] - a[1:] b0,  I - Aᵀ = [[1+a1, -1], [a2, 1]]
    const B0 = b1 - a1 * b0, B1 = b2 - a2 * b0;
    const det = (1 + a1) * 1 + a2;
    const z0 = (B0 + B1) / det;
    const z1 = B1 - a2 * z0;
    const zi = [scale * z0, scale * z1];
    scale *= (b0 + b1 + b2) / (1 + a1 + a2);
    return zi;
  });
}

function sosfilt(sos, x, zi) {
  const y = Float64Array.from(x);
  sos.forEach(([b0, b1, b2, , a1, a2], s) => {
    let [z0, z1] = zi[s];
    for (let i = 0; i < y.length; i++) {
      const xi = y[i];
      const yi = b0 * xi + z0;
      z0 = b1 * xi - a1 * yi + z1;
      z1 = b2 * xi - a2 * yi;
      y[i] = yi;
    }
  });
  return y;
}

// scipy.signal.sosfiltfilt (tek uzatma + durağan başlangıç koşulu), rppg.filtering.bandpass
export function bandpass(x, sos = SOS_HR) {
  const n = x.length;
  if (n < 10) {
    const m = mean(x);
    return x.map((v) => v - m);
  }
  const padlen = Math.min(n - 1, 3 * (2 * sos.length + 1) * 3);
  const ext = [];
  for (let i = padlen; i >= 1; i--) ext.push(2 * x[0] - x[i]);
  for (let i = 0; i < n; i++) ext.push(x[i]);
  for (let i = n - 2; i >= n - 1 - padlen; i--) ext.push(2 * x[n - 1] - x[i]);
  const zi = sosfiltZi(sos);
  let y = sosfilt(sos, ext, zi.map(([a, b]) => [a * ext[0], b * ext[0]]));
  y.reverse();
  y = sosfilt(sos, y, zi.map(([a, b]) => [a * y[0], b * y[0]]));
  y.reverse();
  return Array.from(y.slice(padlen, padlen + n));
}

export function zscore(x) {
  const m = mean(x), s = std(x);
  return x.map((v) => (v - m) / (s > 1e-12 ? s : 1));
}

// rppg.filtering.preprocess_bvp
export const preprocessBvp = (x) => zscore(bandpass(detrendTarvainen(x)));

// rppg.hr.spectrum_bpm — Hann pencereli periyodogram, doğrudan BPM ızgarasında DFT (toplamı 1)
export function spectrumBpm(x, fs = FS, grid = BPM_GRID) {
  const n = x.length, m = mean(x);
  const w = Array.from({ length: n }, (_, i) => (x[i] - m) * (0.5 - 0.5 * Math.cos((2 * Math.PI * i) / n)));
  const p = grid.map((bpm) => {
    const om = (2 * Math.PI * bpm) / 60 / fs;
    let re = 0, im = 0;
    for (let i = 0; i < n; i++) {
      re += w[i] * Math.cos(om * i);
      im -= w[i] * Math.sin(om * i);
    }
    return re * re + im * im;
  });
  const s = p.reduce((a, b) => a + b, 0);
  return s > 0 ? p.map((v) => v / s) : p.map(() => 1 / grid.length);
}

// rppg.hr.peak_bpm — parabolik alt-bin tepe
export function peakBpm(grid, p) {
  let i = 0;
  for (let k = 1; k < p.length; k++) if (p[k] > p[i]) i = k;
  if (i > 0 && i < p.length - 1) {
    const a = p[i - 1], b = p[i], c = p[i + 1], d = a - 2 * b + c;
    if (Math.abs(d) > 1e-15) return grid[i] + 0.5 * ((a - c) / d) * (grid[1] - grid[0]);
  }
  return grid[i];
}

// rppg.hr.window_snr_from_spectrum (dB)
export function windowSnr(grid, p, hr) {
  let s = 0, nse = 0;
  grid.forEach((g, i) => {
    if (Math.abs(g - hr) <= 6 || Math.abs(g - 2 * hr) <= 12) s += p[i];
    else nse += p[i];
  });
  return 10 * Math.log10((s + 1e-12) / (nse + 1e-12));
}

// rppg.hr.OnlineHRTracker — Viterbi'nin çevrimiçi (ileri Bayes) eşi
export class OnlineHRTracker {
  constructor(grid = BPM_GRID, maxRateBpmS = 4) {
    this.grid = grid;
    this.rate = maxRateBpmS;
    this.reset();
  }
  reset() {
    this.belief = this.grid.map(() => 1 / this.grid.length);
  }
  update(p, dt = 1, conf = 1) {
    const sigma = Math.max(1.5, this.rate * dt);
    const step = this.grid[1] - this.grid[0];
    const k = Math.ceil((4 * sigma) / step);
    const kern = [];
    for (let j = -k; j <= k; j++) kern.push(Math.exp(-0.5 * ((j * step) / sigma) ** 2));
    const ks = kern.reduce((a, b) => a + b, 0);
    const F = this.grid.length;
    const pmax = Math.max(...p) + 1e-15;
    let tot = 0;
    const post = new Array(F);
    for (let i = 0; i < F; i++) {
      let pred = 0;
      for (let j = -k; j <= k; j++) {
        const q = i - j;
        if (q >= 0 && q < F) pred += this.belief[q] * kern[j + k];
      }
      pred = pred / ks + 1e-9;
      post[i] = pred * Math.pow(p[i] / pmax + 1e-6, conf);
      tot += post[i];
    }
    this.belief = post.map((v) => v / tot);
    return peakBpm(this.grid, this.belief);
  }
}

// rppg.fusion.motion_confidence (çevrimiçi): c = 1 / (1 + (m / (2·medyan))²)
export function motionConfidence(m, history, floor = 0.1) {
  const h = [...history].sort((a, b) => a - b);
  const med = h.length ? h[Math.floor(h.length / 2)] : m;
  const c = 1 / (1 + (m / (2 * med + 1e-9)) ** 2);
  return Math.min(1, Math.max(floor, c / 0.8)); // hareketsizken c ≈ 0.8 -> 1'e ölçekle
}

// Bir analiz penceresi: RGB örnekleri (zaman damgalı) -> BVP, spektrum
export function analyzeWindow(t, rgb, { method = "pos", channel = 1 } = {}) {
  const u = resampleUniform(t, rgb, FS);
  const raw = method === "pos" ? pos(u) : u.map((p) => p[channel]);
  const bvp = preprocessBvp(raw);
  const spec = spectrumBpm(bvp);
  return { bvp, spec, n: u.length };
}
