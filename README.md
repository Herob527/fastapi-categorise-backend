## PREREQUISITES

- Python 3.12
- Poetry

## LOCAL

0. Install uv: [installation steps](https://docs.astral.sh/uv/getting-started/installation/#installation-methods)
1. Create venv: `python -m venv .venv`
2. Activate venv: `source .venv/bin/activate`
3. Install dependencies: `uv pip install`
4. Run: `uvicorn main:app --reload`

## DOCKER

- Build: `docker build  -t 'backend' .`
- Run: `docker run -p 80:80 --rm backend`
