"""VEYRA — détecteur de texte expérimental (fonction Vercel, gratuit).

Modèle : almanach/camemberta-chatgptdetect-noisy, converti en ONNX int8 (français ;
ses auteurs le réservent à la recherche). Renvoie un score brut 0..1 ; l'interprétation
(seuils, conclusion) est faite par l'API VEYRA. Accès protégé par une clé partagée.
"""
import hmac
import os
from pathlib import Path

import numpy as np
import onnxruntime as ort
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from tokenizers import Tokenizer

HERE = Path(__file__).parent / "model"
MAX_CHARS = 20_000
SIZE, STRIDE, MAX_CHUNKS = 510, 450, 12
app = FastAPI(title="VEYRA text detector", docs_url=None, redoc_url=None, openapi_url=None)
_state: dict = {}


def _load():
    if not _state:
        tok = Tokenizer.from_file(str(HERE / "tokenizer.json"))
        tok.no_truncation()
        tok.no_padding()
        opts = ort.SessionOptions()
        opts.intra_op_num_threads = 2
        _state["tok"] = tok
        _state["sess"] = ort.InferenceSession(str(HERE / "model_q8.onnx"), opts,
                                              providers=["CPUExecutionProvider"])
        _state["cls"] = tok.token_to_id("[CLS]")
        _state["sep"] = tok.token_to_id("[SEP]")
    return _state


def _chunks(ids):
    if len(ids) <= SIZE:
        return [ids]
    out = [ids[s:s + SIZE] for s in range(0, len(ids) - SIZE + 1, STRIDE)]
    if (len(ids) - SIZE) % STRIDE:
        out.append(ids[-SIZE:])
    return out[:MAX_CHUNKS]


class Req(BaseModel):
    text: str


@app.get("/")
def health():
    return {"status": "ok"}


@app.post("/detect")
def detect(req: Req, x_veyra_key: str = Header(default="")):
    key = os.getenv("VEYRA_DETECTOR_KEY", "")
    if not key or not hmac.compare_digest(x_veyra_key.encode(), key.encode()):
        raise HTTPException(status_code=401, detail="unauthorized")
    s = _load()
    ids = s["tok"].encode(req.text.strip()[:MAX_CHARS], add_special_tokens=False).ids
    if not ids:
        raise HTTPException(status_code=422, detail="empty")
    scores = []
    for c in _chunks(ids):
        x = np.array([[s["cls"]] + c + [s["sep"]]], dtype=np.int64)
        logits = s["sess"].run(None, {"input_ids": x, "attention_mask": np.ones_like(x)})[0][0]
        e = np.exp(logits - logits.max())
        scores.append(float(e[1] / e.sum()))
    return {"score": sum(scores) / len(scores), "chunks": len(scores)}
