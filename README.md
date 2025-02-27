## PREREQUISITES

- Python 3.12
- Poetry

## LOCAL

0. Install poetry: `pip install poetry`
1. Create venv: `python -m venv .venv`
2. Activate venv: `source .venv/bin/activate`
3. Install dependencies: `poetry install`
4. Run: `uvicorn main:app --reload`

## DOCKER

- Build: `docker build  -t 'backend' .`
- Run: `docker run -p 80:80 --rm --network host backend`
