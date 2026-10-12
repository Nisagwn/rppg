// Model girdisinin hazırlanması iki adıma bölünür:
//   planWindow (ana iş parçacığı): hangi karelerin hangi ağırlıkla karışacağı — yalnızca zaman damgaları, ucuz.
//   packWindow (Web Worker):        [3, T, 72, 72] float32 tensörünün doldurulması — ~2.5 M değer, 10 MB.
// Böylece her pencerede ana iş parçacığında 10 MB ayırma ve uzun döngü olmaz; sonuç tek parçalı hesapla bit bit aynıdır.

// F: [{ t, px }] (zamana göre sıralı), kareler t0 + (k0 + i) / fs anlarına doğrusal enterpole edilir.
// Dönüş: { lo, hi, ia, w } — kullanılan kareler F[lo..hi], i. örnek = px[ia[i]]·(1−w[i]) + px[ia[i]+1]·w[i].
// Kare aralığı maxGap'ten büyükse (yüz kayboldu / kare atlandı) null.
export function planWindow(F, t0, k0, T, fs, maxGap) {
  const ia = new Int32Array(T), w = new Float64Array(T);
  let j = 0, lo = -1;
  for (let i = 0; i < T; i++) {
    const t = t0 + (k0 + i) / fs;
    while (j < F.length - 2 && F[j + 1].t <= t) j++;
    const a = F[j], b = F[j + 1];
    if (b.t - a.t > maxGap) return null;
    if (lo < 0) lo = j;
    ia[i] = j - lo;
    w[i] = Math.min(1, Math.max(0, (t - a.t) / (b.t - a.t || 1)));
  }
  return { lo, hi: lo + ia[T - 1] + 1, ia, w };
}

// px: planWindow'un seçtiği karelerin 72x72x3 Uint8 kırpıntıları (F[lo..hi]). Çıktı: kanal-önce [3, T, P].
export function packWindow(px, ia, w, T, P) {
  const out = new Float32Array(3 * T * P);
  for (let i = 0; i < T; i++) {
    const a = px[ia[i]], b = px[ia[i] + 1], wi = w[i];
    for (let p = 0, q = 0; p < P; p++, q += 3) {
      for (let c = 0; c < 3; c++) out[c * T * P + i * P + p] = a[q + c] * (1 - wi) + b[q + c] * wi;
    }
  }
  return out;
}
