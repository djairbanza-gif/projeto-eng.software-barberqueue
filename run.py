"""Ponto de entrada: execute `python run.py` e acesse http://127.0.0.1:5000"""
from backend.app import create_app

if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=5000, debug=True)
