# Use the venv interpreter when there is one; plain python3 otherwise.
PY := $(shell [ -x .venv/bin/python ] && echo .venv/bin/python || echo python3)

.PHONY: setup assets test audit serve ca-bundle
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

ca-bundle:
	@$(PY) -c "import certifi,sys;sys.stdout.write(open(certifi.where()).read())" > ca-bundle.pem
	@if [ -f "$$HOME/company-ca-bundle.pem" ]; then \
		cat "$$HOME/company-ca-bundle.pem" >> ca-bundle.pem; \
		echo "wrote ca-bundle.pem (certifi + $$HOME/company-ca-bundle.pem)"; \
	else \
		echo "wrote ca-bundle.pem (certifi only; no ~/company-ca-bundle.pem found)"; \
	fi
	@echo 'now add  SHADESPAN_CA_BUNDLE=ca-bundle.pem  to your .env'
