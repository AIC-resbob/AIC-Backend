a backend server for THIS AIC project


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
    ├── database.py
    ├── db_models.py
    ├── main.py
    ├── middleware.py
    ├── models
    │   ├── discount_demand_response_model.joblib
    │   ├── discount_engine_meta.joblib
    │   ├── restock_predictor_meta.joblib
    │   └── restock_predictor_model.joblib
    ├── __pycache__
    │   ├── database.cpython-312.pyc
    │   ├── db_models.cpython-312.pyc
    │   ├── main.cpython-312.pyc
    │   └── middleware.cpython-312.pyc
    

5 directories, 25 files
```
