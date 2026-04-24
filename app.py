from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Hello! Your server is working! 🎉"

@app.route('/login')
def login():
    return "Login page would be here"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
