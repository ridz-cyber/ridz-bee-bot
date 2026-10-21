from flask import Flask
app = Flask(__name__)

@app.route('/')
def home():
    return 'Ridz Bee Bot is AWAKE! Live Ready!'

@app.route('/api')
def api():
    return 'Bee API working'
