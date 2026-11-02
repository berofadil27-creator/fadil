"""Régénère model/ (ONNX int8, poids en fichiers séparés < 100 Mo pour Vercel).
Usage : pip install torch transformers onnx onnxruntime ; python scripts/build_model.py"""
import torch, onnx
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from onnxruntime.quantization import quantize_dynamic, QuantType
M = "almanach/camemberta-chatgptdetect-noisy"
out = Path(__file__).resolve().parent.parent / "model"; out.mkdir(exist_ok=True)
tok = AutoTokenizer.from_pretrained(M); model = AutoModelForSequenceClassification.from_pretrained(M).eval()
tok.backend_tokenizer.save(str(out / "tokenizer.json"))
x = tok("Bonjour.", return_tensors="pt")
torch.onnx.export(model, (x["input_ids"], x["attention_mask"]), "/tmp/m.onnx", input_names=["input_ids", "attention_mask"],
                  output_names=["logits"], dynamic_axes={"input_ids": {0: "b", 1: "s"}, "attention_mask": {0: "b", 1: "s"}},
                  opset_version=17, dynamo=False)
quantize_dynamic("/tmp/m.onnx", "/tmp/q.onnx", weight_type=QuantType.QInt8)
onnx.save_model(onnx.load("/tmp/q.onnx"), str(out / "model_q8.onnx"), save_as_external_data=True,
                all_tensors_to_one_file=False, size_threshold=1024)
