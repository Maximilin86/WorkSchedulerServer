from flask import Flask, request, jsonify, render_template
from database import ws_db

app = Flask(__name__)

countries = [
    {"id": 1, "name": "Thailand", "capital": "Bangkok", "area": 513120},
    {"id": 2, "name": "Australia", "capital": "Canberra", "area": 7617930},
    {"id": 3, "name": "Egypt", "capital": "Cairo", "area": 1010408},
]


@app.route('/')
def index():
    return jsonify(ws_db.get_users())


@app.get("/countries")
def get_countries():
    return jsonify(countries)


def _find_next_id():
    return max(country["id"] for country in countries) + 1


@app.post("/countries")
def add_country():
    if not request.is_json:
        return {"error": "Request must be JSON"}, 415
    country = request.get_json()
    country["id"] = _find_next_id()
    countries.append(country)
    return country, 201


@app.post("/login")
def login():
    if not request.is_json:
        return {"error": "Request must be JSON"}, 415
    form = request.get_json()
    try:
        username = form['user']
        password = form['password']
    except ValueError:
        return {"error": "Invalid json fields"}, 415
    user = ws_db.find_user(username, password)
    if user is None:
        return {'error': 'User not found'}
    token = ws_db.start_user_session(user['id'])
    return {**user, 'token': token}


