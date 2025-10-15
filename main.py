import os

from flask import Flask, send_from_directory
from src.steam_tables.routes import steam_tables_blueprint

app = Flask(__name__, static_folder="src/static")

app.register_blueprint(steam_tables_blueprint)


@app.route("/")
def index():
    return send_from_directory("src", "index.html")


@app.route("/manifest.json")
def manifest():
    return send_from_directory("src", "manifest.json")


@app.route("/service-worker.js")
def service_worker():
    return send_from_directory("src", "service-worker.js")


def main():
    app.run(port=int(os.environ.get("PORT", 80)))


if __name__ == "__main__":
    main()
