## LOCAL
0. Install poetry (`pip install poetry`)
1. Create venv (`python -m venv .venv`)
2. Activate venv (`source .venv/bin/activate`)
3. Install dependencies (`poetry install`)
4. Run: `uvicorn main:app --reload`


## DOCKER
- Build: `sudo docker build  -t 'backend' .`
- Run: `sudo docker run -p 8000:8000 --rm --network host backend`
