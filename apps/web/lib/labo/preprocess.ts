// Prétraitement Community Forensics (ViT-S 384), identique à la référence Python/PIL :
// redimensionnement BILINEAR de Pillow (petit côté = 440 px, filtre triangle élargi en réduction,
// arithmétique entière 8 bits comme Pillow), recadrage central 384x384, /255, normalisation ImageNet, CHW.
// Code pur (sans DOM) : utilisable dans le navigateur et dans Node pour la validation.

export const INPUT_SIZE = 384;
const SHORT_SIDE = 440;
const MEAN = [0.485, 0.456, 0.406];
const STD = [0.229, 0.224, 0.225];
const PRECISION_BITS = 32 - 8 - 2;
const ONE = 2 ** PRECISION_BITS;
const HALF = 2 ** (PRECISION_BITS - 1);

/** round() de Python (arrondi au pair). */
function pyRound(x: number): number {
  const f = Math.floor(x);
  const d = x - f;
  if (d > 0.5) return f + 1;
  if (d < 0.5) return f;
  return f % 2 === 0 ? f : f + 1;
}

function bilinear(x: number): number {
  if (x < 0) x = -x;
  return x < 1 ? 1 - x : 0;
}

interface Coeffs { bounds: Int32Array; ksize: number; k: Float64Array }

/** Reproduit precompute_coeffs + normalize_coeffs_8bpc de Pillow (Resample.c). */
function coeffs(inSize: number, outSize: number): Coeffs {
  const scale = inSize / outSize;
  const filterscale = Math.max(scale, 1);
  const support = 1 * filterscale;
  const ksize = Math.ceil(support) * 2 + 1;
  const k = new Float64Array(outSize * ksize);
  const bounds = new Int32Array(outSize * 2);
  const ss = 1 / filterscale;
  for (let xx = 0; xx < outSize; xx++) {
    const center = (xx + 0.5) * scale;
    let ww = 0;
    const xmin = Math.max(Math.trunc(center - support + 0.5), 0);
    const xmax = Math.min(Math.trunc(center + support + 0.5), inSize) - xmin;
    const base = xx * ksize;
    let x = 0;
    for (; x < xmax; x++) {
      const w = bilinear((x + xmin - center + 0.5) * ss);
      k[base + x] = w;
      ww += w;
    }
    for (x = 0; x < xmax; x++) if (ww !== 0) k[base + x] /= ww;
    for (; x < ksize; x++) k[base + x] = 0;
    bounds[xx * 2] = xmin;
    bounds[xx * 2 + 1] = xmax;
  }
  for (let i = 0; i < k.length; i++) {
    const v = k[i] * ONE;
    k[i] = v < 0 ? Math.trunc(-0.5 + v) : Math.trunc(0.5 + v);
  }
  return { bounds, ksize, k };
}

function clip8(v: number): number {
  const r = Math.floor(v / ONE);
  return r < 0 ? 0 : r > 255 ? 255 : r;
}

/**
 * rgba : pixels RGBA (ImageData.data) ou RGB (channels = 3) de taille width x height.
 * Renvoie un Float32Array [3, 384, 384] prêt pour l'entrée 'x' du modèle.
 */
export function preprocess(rgba: Uint8ClampedArray | Uint8Array, width: number, height: number, channels = 4): Float32Array {
  const k = SHORT_SIDE / Math.min(width, height);
  const outW = pyRound(width * k);
  const outH = pyRound(height * k);
  if (outW < INPUT_SIZE || outH < INPUT_SIZE) throw new Error("Image trop petite");
  const left = Math.floor((outW - INPUT_SIZE) / 2);
  const top = Math.floor((outH - INPUT_SIZE) / 2);

  const ch = coeffs(width, outW);
  const cv = coeffs(height, outH);

  // Lignes d'entrée nécessaires pour les lignes de sortie top..top+383.
  const yFirst = cv.bounds[top * 2];
  const yLast = cv.bounds[(top + INPUT_SIZE - 1) * 2] + cv.bounds[(top + INPUT_SIZE - 1) * 2 + 1];
  const rows = yLast - yFirst;

  // Passe horizontale (colonnes left..left+383 seulement), résultat 8 bits comme Pillow.
  const tmp = new Uint8Array(rows * INPUT_SIZE * 3);
  for (let y = 0; y < rows; y++) {
    const rowOff = (y + yFirst) * width * channels;
    for (let xo = 0; xo < INPUT_SIZE; xo++) {
      const xx = xo + left;
      const xmin = ch.bounds[xx * 2];
      const xmax = ch.bounds[xx * 2 + 1];
      const kb = xx * ch.ksize;
      let s0 = HALF, s1 = HALF, s2 = HALF;
      for (let x = 0; x < xmax; x++) {
        const w = ch.k[kb + x];
        const p = rowOff + (x + xmin) * channels;
        s0 += rgba[p] * w;
        s1 += rgba[p + 1] * w;
        s2 += rgba[p + 2] * w;
      }
      const o = (y * INPUT_SIZE + xo) * 3;
      tmp[o] = clip8(s0);
      tmp[o + 1] = clip8(s1);
      tmp[o + 2] = clip8(s2);
    }
  }

  // Passe verticale + normalisation, sortie CHW.
  const plane = INPUT_SIZE * INPUT_SIZE;
  const out = new Float32Array(3 * plane);
  for (let yo = 0; yo < INPUT_SIZE; yo++) {
    const yy = yo + top;
    const ymin = cv.bounds[yy * 2] - yFirst;
    const ymax = cv.bounds[yy * 2 + 1];
    const kb = yy * cv.ksize;
    for (let xo = 0; xo < INPUT_SIZE; xo++) {
      let s0 = HALF, s1 = HALF, s2 = HALF;
      for (let y = 0; y < ymax; y++) {
        const w = cv.k[kb + y];
        const p = ((y + ymin) * INPUT_SIZE + xo) * 3;
        s0 += tmp[p] * w;
        s1 += tmp[p + 1] * w;
        s2 += tmp[p + 2] * w;
      }
      const i = yo * INPUT_SIZE + xo;
      out[i] = (clip8(s0) / 255 - MEAN[0]) / STD[0];
      out[plane + i] = (clip8(s1) / 255 - MEAN[1]) / STD[1];
      out[2 * plane + i] = (clip8(s2) / 255 - MEAN[2]) / STD[2];
    }
  }
  return out;
}

export function sigmoid(x: number): number {
  return 1 / (1 + Math.exp(-x));
}
