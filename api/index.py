from flask import Flask, request
app = Flask(__name__)

@app.route('/')
def home():
    return 'Ridz Bot Live!'

@app.route('/webhook', methods=['POST'])
def webhook():
    return 'ok'

if __name__ == '__main__':
    app.run()
