import os
from cors import crossdomain
from flask import Flask, jsonify, request, send_from_directory

from train import complete
from train import get_model


def read_models(base_path="models/"):
    return set([x.split(".")[0] for x in os.listdir(base_path)])


app = Flask(__name__, static_folder='../ui/build', )

models = {x: get_model(x) for x in read_models()}


def get_args(req):
    if request.method == 'POST':
        args = request.json
    elif request.method == "GET":
        args = request.args
    return args


@app.route("/predict", methods=["GET", "POST", "OPTIONS"])
@crossdomain(origin='*', headers="Content-Type")
def predict():
    args = get_args(request)
    sentence = args.get("keyword", "from ")
    model_name = args.get("model", "char")
    if model_name not in models:
        models[model_name] = get_model(model_name)
    suggestions = complete(models[model_name], sentence, [0.2, 0.5, 1])
    return jsonify({"data": {"results": [x.strip() for x in suggestions]}})


@app.route("/get_models", methods=["GET", "POST", "OPTIONS"])
@crossdomain(origin='*', headers="Content-Type")
def get_models():
    return jsonify({"data": {"results": list(models)}})


@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('../ui/build/static', path)


@app.route('/', methods=['GET'])
def index():
    return app.send_static_file('index.html')


@app.route('/manifest.json', methods=['GET'])
def manifest():
    return app.send_static_file('manifest.json')


@app.route('/favicon.ico', methods=['GET'])
def favicon():
    return app.send_static_file('favicon.ico')


def main(host="0.0.0.0", port=9078):
    app.run(host=host, port=port, debug=True)


if __name__ == "__main__":
    main()
