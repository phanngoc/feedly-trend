from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from peewee import IntegrityError
from models.database_models import db, User, Feed, Subscription

app = Flask(__name__)

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    
    if not name or not email or not password:
        return jsonify({'error': 'Missing required fields'}), 400
    
    password_hash = generate_password_hash(password)
    
    try:
        with db.atomic():
            user = User.create(name=name, email=email, password_hash=password_hash)
        return jsonify({'message': 'User registered successfully'}), 201
    except IntegrityError:
        return jsonify({'error': 'Email already registered'}), 400

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'error': 'Missing required fields'}), 400
    
    try:
        user = User.get(User.email == email)
        if check_password_hash(user.password_hash, password):
            return jsonify({'message': 'Login successful'}), 200
        else:
            return jsonify({'error': 'Invalid credentials'}), 401
    except User.DoesNotExist:
        return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/register_feed', methods=['POST'])
def register_feed():
    data = request.get_json()
    title = data.get('title')
    url = data.get('url')
    description = data.get('description')
    language = data.get('language')
    
    if not title or not url:
        return jsonify({'error': 'Missing required fields'}), 400
    
    try:
        with db.atomic():
            feed = Feed.create(title=title, url=url, description=description, language=language)
        return jsonify({'message': 'Feed registered successfully'}), 201
    except IntegrityError:
        return jsonify({'error': 'Feed URL already registered'}), 400

@app.route('/api/subscriptions', methods=['GET'])
def get_subscriptions():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'error': 'Missing user_id'}), 400

    subscriptions = Subscription.select().where(Subscription.user_id == user_id)
    subscriptions_data = [
        {
            'id': subscription.id,
            'feed': {
                'id': subscription.feed.id,
                'title': subscription.feed.title,
                'url': subscription.feed.url,
                'description': subscription.feed.description,
                'language': subscription.feed.language,
            }
        }
        for subscription in subscriptions
    ]
    return jsonify(subscriptions_data), 200

if __name__ == '__main__':
    app.run(debug=True)
