from flask import Flask, request, jsonify, render_template
from database import ws_db, ws_user, ws_session, ws_permissions

app = Flask(__name__)

countries = [
    {"id": 1, "name": "Thailand", "capital": "Bangkok", "area": 513120},
    {"id": 2, "name": "Australia", "capital": "Canberra", "area": 7617930},
    {"id": 3, "name": "Egypt", "capital": "Cairo", "area": 1010408},
]


@app.route('/')
def index():
    return '''
<p>Привет! это простой REST сервер проекта!</p>
<a href="/users">users</a></br>
<a href="/login">login</a>
'''


@app.get('/users')
def get_users():
    return jsonify(ws_user.get_users())


@app.get('/sessions')
def get_sessions():
    return jsonify(ws_session.get_sessions())


@app.post("/login")
def login():
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 415
    form = request.get_json()
    try:
        username = form['user']
        password = form['password']
    except ValueError:
        return jsonify({"error": "Invalid json fields"}), 415
    user = ws_user.find_user_by_auth(username, password)
    if user is None:
        return jsonify({'error': 'User is not found'})
    token = ws_session.start_user_session(user.id)
    return jsonify({'token': token})


@app.post("/get_username")
def get_username():
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 415
    form = request.get_json()
    try:
        token = form['token']
    except ValueError:
        return jsonify({"error": "Invalid json fields"}), 415
    session = ws_session.find_session_by_token(token)
    if session is None:
        return jsonify({'error': 'Session is not found'})
    user = ws_user.get_user(session.user_id)
    if user is None:
        return jsonify({'error': 'User is not found'})
    return jsonify({
        'first_name': user.first_name,
        'last_name': user.last_name,
        'fathers_name': user.fathers_name
    })


@app.post("/get_permissions")
def get_permissions():
    if not request.is_json:
        return {"error": "Request must be JSON"}, 415
    form = request.get_json()
    try:
        token = form['token']
    except ValueError:
        return jsonify({"error": "Invalid json fields"}), 415
    session = ws_session.find_session_by_token(token)
    if session is None:
        return jsonify({'error': 'Session is not found'})
    user = ws_user.get_user(session.user_id)
    if user is None:
        return jsonify({'error': 'User is not found'})
    perms = ws_permissions.get_permissions(user.role)
    return jsonify({
        'permissions': perms,
    })


@app.post("/list_users")
def list_users():
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 415
    form = request.get_json()
    try:
        token = form['token']
    except ValueError:
        return jsonify({"error": "Invalid json fields"}), 415
    session = ws_session.find_session_by_token(token)
    if session is None:
        return jsonify({'error': 'Session is not found'})
    user = ws_user.get_user(session.user_id)
    if user is None:
        return jsonify({'error': 'User is not found'})
    if not ws_permissions.has_permission(user.role, ws_permissions.Permission.QUERY_USERS):
        return jsonify({'error': 'User has no permission'})
    return jsonify({
        'first_name': user.first_name,
        'last_name': user.last_name,
        'fathers_name': user.fathers_name
    })


