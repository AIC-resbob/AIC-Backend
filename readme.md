a backend server for THIS AIC project

API Docs : aic.elysiavernight.com/docs
## how to use
1. git clone this repo
```git clone https://github.com/AIC-resbob/AIC-backend```
```cd AIC-backend```
2. Create and install a python environment if you don't have one
For Linux
```python -m venv .venv```
```source .venv/bin/activate```
3. Do ```pip install -r requirements.txt```
4. for Linux users use ```sh run.sh```, for winslop just run the ```run.bat```


## Project Structure
Get the AI-Model from https://github.com/AIC-resbob/AIC
```
.
├── app.db
├── docker-compose.yml
├── Dockerfile
├── .dockerignore
├── .env
├── .env.example
├── .gitignore
├── readme.md
├── requirements.txt
├── run.bat
├── run.sh
└── src
    ├── auth
    │   ├── router.py
    │   ├── schemas.py
    │   └── utils.py
    ├── database.py
    ├── db_models.py
    ├── discount
    │   ├── __init__.py
    │   ├── router.py
    │   ├── schemas.py
    │   └── service.py
    ├── main.py
    ├── middleware.py
    ├── models
    │   ├── discount_demand_response_model.joblib
    │   ├── discount_engine_meta.joblib
    │   ├── restock_predictor_meta.joblib
    │   └── restock_predictor_model.joblib
    ├── products
    │   ├── __init__.py
    │   ├── router.py
    │   └── schemas.py
    ├── restock
    │   ├── __init__.py
    │   ├── router.py
    │   ├── schemas.py
    │   └── service.py
    └── transactions
        ├── __init__.py
        ├── router.py
        └── schemas.py

8 directories, 36 files
```
