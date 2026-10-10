.PHONY: setup test run-api check-data clean

PYTHON = python
VENV_PYTHON = ./venv/Scripts/python
VENV_PYTEST = ./venv/Scripts/pytest
VENV_UVICORN = ./venv/Scripts/uvicorn

setup:
	$(PYTHON) -m venv venv
	$(VENV_PYTHON) -m pip install --upgrade pip
	$(VENV_PYTHON) -m pip install -r requirements.txt
	$(VENV_PYTHON) -m spacy download en_core_web_sm
	$(VENV_PYTHON) scripts/generate_fixtures.py

test:
	$(VENV_PYTEST) -v

run-api:
	$(VENV_UVICORN) api.main:app --reload --host 127.0.0.1 --port 8000

check-data:
	$(VENV_PYTHON) scripts/check_data.py

clean:
	rm -rf __pycache__ .pytest_cache cache
