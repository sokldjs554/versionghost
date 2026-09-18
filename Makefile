.PHONY: test demo run evaluate clean

test:
	python -m pytest -q

demo:
	python -m versionghost.cli demo

run:
	uvicorn versionghost.main:app --host 0.0.0.0 --port $${PORT:-8000}

evaluate:
	python scripts/evaluate_demo.py

clean:
	rm -rf .versionghost .pytest_cache artifacts/evaluation.json
