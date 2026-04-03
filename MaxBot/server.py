from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json

    print("ПРИШЁЛ UPDATE:")
    print(data)

    # тут будет логика бота
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(port=5000)