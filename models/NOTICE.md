# CyberSRS model provenance

The runtime release contains the quantized CyberSRS model from the local
`cybersrs-qwen3-4b-ft:latest` Ollama tag. CyberSRS fine-tuning and quantization
produce a modified model based on
[Qwen3-4B-Instruct-2507](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507).
The [upstream Apache 2.0 license](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507/blob/main/LICENSE)
and Alibaba Cloud attribution are preserved in `CyberSRS.Modelfile`.

`runtime-model.json` identifies each release part and the assembled GGUF by
SHA-256. The installer verifies these bytes before importing the model with
the original template and generation parameters.
