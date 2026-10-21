from flask import Flask

app = Flask(__name__)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    return '🐝 Ridz Bee Bot is AWAKE! Live Ready!'

# Vercel needs this
app = app
