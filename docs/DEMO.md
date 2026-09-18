# Demo Walkthrough

## 30–45 second reviewer path

1. Open the home screen and read the one-line problem: **change the API without guessing which old clients broke**.
2. Keep the built-in request and click **Run compatibility pipeline**.
3. Watch the stage trace move through impact → contract → patch → verify.
4. The first attempt is rejected: v2 works, while legacy clients/cross-version behavior expose compatibility errors.
5. The repair stage appears automatically.
6. The same client matrix is replayed; all six probes pass.
7. Open the requirement ledger: REQ-1 through REQ-5 each points to passing evidence.
8. Show the blast-radius panel and merge-packet metrics.

The demo is intentionally not a chat window. The visual center is the client-version compatibility matrix and the rejected/repair attempt trail.

## Local run

```bash
python -m pip install -e .
uvicorn versionghost.main:app --reload
```

Open `http://127.0.0.1:8000`.

## Keyless CLI path

```bash
python -m versionghost.cli demo > merge-packet.json
```

The default route needs no external model key.

## Local open-source model route

Run an OpenAI-compatible local endpoint (for example Ollama) and configure:

```bash
export VERSIONGHOST_OPENAI_BASE_URL=http://127.0.0.1:11434/v1
export VERSIONGHOST_OPENAI_MODEL=qwen2.5-coder:7b
python -m versionghost.cli demo --provider ollama
```

This provider route is optional. Do not present a local-model result as measured until it has actually been run and its packet is saved.
