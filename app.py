from flask import Flask, render_template
import os
import json

app = Flask(__name__)

# A simple data structure to store messages (in real usage, this would be a database)
messages = []

@app.route('/')
def home():
        # Load messages from JSON file
    try:
        with open("messages.json", "r") as file:
            messages = json.load(file)
    except FileNotFoundError:
        messages = []
    return render_template('index.html', messages=messages)


# Function to add messages
def add_message(msg):
    print(msg)
    messages.append(msg)


if __name__ == "__main__":
    app.run(debug=True)

