import json
from flask import Flask, render_template

app = Flask(__name__)

def get_blogs():
    with open('blogs.json', 'r') as f:
        return json.load(f)

@app.route("/")
def index():
    blogs = get_blogs()
    return render_template('home.html', blogs=blogs)

if __name__ == "__main__":
    app.run(debug=True)