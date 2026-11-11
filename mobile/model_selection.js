// Yalnızca paketle gelen modeller seçilebilir; URL'den keyfi dosya yüklenmez.
const MODELS = Object.freeze({
  tur5: Object.freeze({ key: "tur5", label: "Mevcut", file: "./model/factorizephys.onnx" }),
  pure: Object.freeze({ key: "pure", label: "PURE S1", file: "./model/mmrphys_pure_s1.onnx" }),
});

export function selectModel(key) {
  return Object.hasOwn(MODELS, key) ? MODELS[key] : MODELS.tur5;
}
