import json
from flask import Flask, render_template, request, jsonify
from supabase import create_client, Client
import os
from dotenv import load_dotenv
from functools import wraps

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Initialize Supabase client
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

# Protect Routes
def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'No authorization header'}), 401

        try:
            token = auth_header.split(' ')[1]
            user = supabase.auth.get_user(token)
            return f(*args, **kwargs)
        except Exception as e:
            return jsonify({'error': 'Invalid token'}), 401

    return decorated

# Route to Fetch All Blogs
@app.route('/blogs', methods=['GET'])
def get_blogs():
    try:
        response = supabase.table('blogs').select('*').eq('is_published', True).execute()
        return jsonify(response.data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Route to Fetch a Single Blog
@app.route('/blogs/<slug>', methods=['GET'])
def get_blog(slug):
    try:
        response = supabase.table('blogs').select('*').eq('slug', slug).execute()
        if response.data:
            return jsonify(response.data[0])
        return jsonify({'error': 'Blog not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Route to Create a New Blog
@app.route('/blogs', methods=['POST'])
@require_auth
def create_blog():
    try:
        data = request.json
        # Get user from token
        auth_header = request.headers.get('Authorization')
        user = supabase.auth.get_user(auth_header.split(' ')[1])

        response = supabase.table('blogs').insert({
            'title': data['title'],
            'slug': data['slug'],
            'content': data['content'],
            'description': data['description'],
            'author_id': user.user.id,
            'is_published': data.get('is_published', True)
        }).execute()
        return jsonify(response.data), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Route to Update a Blog
@app.route('/blogs/<int:blog_id>', methods=['PUT'])
@require_auth
def update_blog(blog_id):
    try:
        data = request.json
        response = supabase.table('blogs').update({
            'title': data['title'],
            'content': data['content'],
            'description': data['description'],
            'is_published': data.get('is_published', True)
        }).eq('id', blog_id).execute()
        return jsonify(response.data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Route to Delete a Blog
@app.route('/blogs/<int:blog_id>', methods=['DELETE'])
@require_auth
def delete_blog(blog_id):
    try:
        response = supabase.table('blogs').delete().eq('id', blog_id).execute()
        return jsonify({'message': 'Blog deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Sign Up Route
@app.route('/signup', methods=['POST'])
def signup():
    try:
        data = request.json
        response = supabase.auth.sign_up({
            'email': data['email'],
            'password': data['password']
        })
        return jsonify(response)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Login Route
@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.json
        response = supabase.auth.sign_in_with_password({
            'email': data['email'],
            'password': data['password']
        })
        return jsonify(response)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Upload File Route
@app.route('/upload', methods=['POST'])
@require_auth
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        response = supabase.storage.from_('blog-images').upload(
            f"images/{file.filename}",
            file
        )
        public_url = supabase.storage.from_('blog-images').get_public_url(
            f"images/{file.filename}"
        )
        return jsonify({'url': public_url})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Static Pages
@app.route("/")
def home():
    try:
        response = supabase.table('blogs').select('*').eq('is_published', True).execute()
        return render_template("home.html", blogs=response.data)
    except Exception as e:
        return render_template("home.html", blogs=[])

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

if __name__ == "__main__":
    app.run(debug=True)