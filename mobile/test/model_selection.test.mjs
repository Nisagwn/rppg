import assert from "node:assert/strict";
import { test } from "node:test";
import { selectModel } from "../model_selection.js";

test("PURE adayı ayrı seçilir, mevcut model varsayılandır", () => {
  assert.equal(selectModel("pure").file, "./model/mmrphys_pure_s1.onnx");
  for (const key of [undefined, null, "", "bilinmeyen", "toString", "__proto__", "https://x/model.onnx", "../x"])
    assert.equal(selectModel(key).key, "tur5");
  assert.equal(selectModel("tur5").file, "./model/factorizephys.onnx");
});
