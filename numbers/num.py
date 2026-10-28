from flask import Flask, jsonify
import random

app = Flask(__name__)

@app.get("/")
def get_random_numbers():
    num1 = random.randint(1, 100)
    num2 = random.randint(1, 100)

    return jsonify({
        "number1": num1,
        "number2": num2
    }), 200


if __name__ == "__main__":
    app.run(debug=True, port=5002)
