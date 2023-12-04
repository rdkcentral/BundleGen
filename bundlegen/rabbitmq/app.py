from flask import Flask
from info import Info

app = Flask(__name__)
app_info = Info()

@app.route("/healthz")
def healthz() -> str:
    return 'OK'

@app.route('/info')
def info():
    return app_info.get()
