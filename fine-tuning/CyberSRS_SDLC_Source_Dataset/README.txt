CyberSRS SDLC Decision Dataset Pack
===================================

PURPOSE
Generate about 300 supervised examples that teach CyberSRS to analyze project
requirements, select an appropriate SDLC/lifecycle approach, justify the choice,
and map requirements into lifecycle activities with secure-development practices.

CONTENTS
- SDLC_Source_Documents/       Trusted source PDFs
- build_sdlc_dataset.py        Resumable Ollama-based dataset generator
- SOURCE_MANIFEST.csv          Source names and official URLs

QUICK START (Windows PowerShell)
1. Extract this whole folder inside your fine-tuning folder.
2. Make sure Ollama is running and your Qwen model exists:
      ollama list
3. Open PowerShell in this extracted folder.
4. Install dependencies once:
      pip install requests pypdf
5. Run:
      python build_sdlc_dataset.py

If your Ollama model has a different name:
      python build_sdlc_dataset.py --model YOUR_MODEL_NAME

DEFAULT MODEL EXPECTED
qwen3:4b-instruct-2507-q4_K_M

OUTPUT
A new folder named sdlc_dataset/ will be created containing:
- train.jsonl
- validation.jsonl
- test.jsonl
- holdout.jsonl
- *_provenance.jsonl files
- dataset_stats.json
- _accepted_checkpoint.jsonl (resume checkpoint)

For target=300 the split is approximately:
- train: 240
- validation: 30
- test: 15
- holdout: 15

IMPORTANT
- Train only on train.jsonl (and use validation.jsonl during training/evaluation).
- Keep test.jsonl and holdout.jsonl unseen for final comparison.
- The examples are SYNTHETIC BUT GROUNDED: the generator uses trusted source
  excerpts plus a curated SDLC decision scaffold. They are not direct quotations.
- The script is resumable. If Ollama returns a 500 error or the machine stops,
  just rerun the same command; it resumes from _accepted_checkpoint.jsonl.
- SWEBOK v4 and ISO/IEC/IEEE 12207 are not redistributed in this ZIP because
  their licensing does not permit us to simply redistribute copies. Their official
  links are listed in SOURCE_MANIFEST.csv as optional references.

FINAL ADAPTER PLAN
Yes: the final intended setup is ONE CyberSRS LoRA/QLoRA adapter trained on a
balanced mixture of your three training datasets:
  1) strict SRS dataset
  2) cybersecurity/networking 200-document dataset
  3) this SDLC-decision dataset
The adapter-training notebook will normalize/balance the three datasets before
training so the larger dataset does not dominate.
