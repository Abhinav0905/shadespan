.PHONY: setup assets test audit serve
setup:
	pip install -e ".[dev]"
assets:
	python scripts/generate_catalog.py
test:
	pytest -q
audit:
	shadespan audit
serve:
	shadespan serve
