import time

from dateutil.relativedelta import relativedelta
from flask import Flask, request, jsonify, render_template

import work_scheduler
import ws_utils
from database import ws_db, ws_user, ws_session, ws_permissions, ws_desire, ws_order

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
<a href="/sessions">sessions</a>
'''


@app.get('/users')
def _get_users():
    return jsonify(ws_user.get_users())


@app.get('/sessions')
def _get_sessions():
    return jsonify(ws_session.get_sessions())


@app.post("/login")
def login():
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 415  # Unsupported Media Type
    form = request.get_json()
    try:
        login = form['login']
        password = form['password']
    except ValueError:
        return jsonify({"error": "Invalid json fields"}), 400  # Bad Request
    # user = ws_user.find_user_by_auth(login, password)
    # if user is None:
    #     return jsonify({'error': 'User is not found'})
    user = ws_user.get_user(1 if login else 3)  # fixme: for debug only

    token = ws_session.start_user_session(user.id)
    display_name = user.first_name
    if user.fathers_name is not None:
        display_name += f' {user.fathers_name}'
    return jsonify({
        'token': token,
        'role': user.role.name.lower(),
        'display-name': display_name
    })


def _check_user(form, required_permission: ws_permissions.Permission) -> tuple[ws_user.UserRow or None, any]:
    try:
        token = form['token']
    except ValueError:
        return None, (jsonify({"error": "Token not found"}), 401)  # Unauthorized
    session = ws_session.find_session_by_token(token)
    if session is None:
        return None, (jsonify({'error': 'Session is not found'}), 401)  # Unauthorized
    user = ws_user.get_user(session.user_id)
    if user is None:
        return None, (jsonify({'error': 'User is not found'}), 401)  # Unauthorized
    if not ws_permissions.has_permission(user.role, required_permission):
        return None, (jsonify({'error': 'User has no permission'}), 403)  # Forbidden
    # time.sleep(1)  # fixme: test fake delay
    return user, None


@app.post("/set_desire")
def set_desire():
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 415  # Unsupported Media Type
    form = request.get_json()
    user, error = _check_user(form, ws_permissions.Permission.MODIFY_DESIRE)
    if error:
        return error
    try:
        date = ws_utils.parse_date(form['date'])
        desire_id = form['desire_id']
        comment = form.get('comment', '')
    except ValueError:
        return jsonify({"error": "Invalid json fields"}), 400  # Bad Request
    desire = None
    if desire_id:
        desire = ws_desire.parse_desire(desire_id)
        if desire is None:
            return jsonify({'error': f'Unknown desire id {desire_id}'})
    ws_desire.set_desire(date, user.id, desire, comment)
    return jsonify({})


@app.post("/set_order")
def set_order():
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 415  # Unsupported Media Type
    form = request.get_json()
    user, error = _check_user(form, ws_permissions.Permission.MODIFY_ORDER)
    if error:
        return error
    try:
        date = ws_utils.parse_date(form['date'])
        target_user_id = form['user_id']
        order_id = form['order_id']
        order = ws_order.Order(order_id) if order_id >= 0 else None
        comment = form.get('comment', '')
    except ValueError:
        return jsonify({"error": "Invalid json fields"}), 400  # Bad Request
    if target_user_id == -1:
        print("set_order", date, 'None', order.name, comment)
        ad_user_id = ws_order.get_all_day_order_user_id(date)
        ws_order.set_order(date, ad_user_id, None, "")
        return jsonify({})
    target_user: ws_user.UserRow = ws_user.get_user(target_user_id)
    if target_user is None:
        return jsonify({'error': 'Target user is not found'}), 400  # Bad Request
    print("set_order", date, f'{target_user.first_name} {target_user.last_name}', order.name, comment)
    ws_order.set_order(date, target_user.id, order, comment)
    return jsonify({})


@app.post("/set_work_orders")
def set_work_orders():
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 415  # Unsupported Media Type
    form = request.get_json()
    user, error = _check_user(form, ws_permissions.Permission.MODIFY_ORDER)
    if error:
        return error
    try:
        date = ws_utils.parse_date(form['date'])
        target_user_ids = form['user_ids']
        comment = form.get('comment', '')
    except ValueError:
        return jsonify({"error": "Invalid json fields"}), 400  # Bad Request
    print("set_work_orders", date, f'{target_user_ids}', comment)
    for target_user_id in target_user_ids:
        target_user: ws_user.UserRow = ws_user.get_user(target_user_id)
        if target_user is None:
            return jsonify({'error': 'Target user is not found'}), 400  # Bad Request
    to_remove: list[int] = []
    current: list[int] = []
    for order in ws_order.get_orders(date):
        if order.order is not ws_order.Order.WORK:
            continue
        if order.user_id not in target_user_ids:
            to_remove.append(order.user_id)
        else:
            current.append(order.user_id)
    to_add: list[int] = []
    for target_user_id in target_user_ids:
        if target_user_id not in current:
            to_add.append(target_user_id)
    for uid in to_remove:
        ws_order.set_order(date, uid, None, comment)
    for uid in to_add:
        ws_order.set_order(date, uid, ws_order.Order.WORK, comment)
    return jsonify({})


@app.post("/get_username")
def get_username():
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 415  # Unsupported Media Type
    form = request.get_json()
    user, error = _check_user(form, ws_permissions.Permission.QUERY_SELF)
    if error:
        return error
    return jsonify({
        'first_name': user.first_name,
        'last_name': user.last_name,
        'fathers_name': user.fathers_name
    })


@app.post("/get_permissions")
def get_permissions():
    if not request.is_json:
        return {"error": "Request must be JSON"}, 415  # Unsupported Media Type
    form = request.get_json()
    user, error = _check_user(form, ws_permissions.Permission.QUERY_SELF)
    if error:
        return error
    perms = ws_permissions.get_permissions(user.role)
    return jsonify({
        'permissions': perms,
    })


@app.post("/get_month_data")
def get_month_data():
    if not request.is_json:
        return {"error": "Request must be JSON"}, 415  # Unsupported Media Type
    form = request.get_json()
    user, error = _check_user(form, ws_permissions.Permission.QUERY_ORDER)
    if error:
        return error
    try:
        date = ws_utils.parse_date(form['date'])
    except ValueError:
        return jsonify({"error": "Invalid json fields"}), 400  # Bad Request
    start = date.replace(day=1)
    end = start + relativedelta(months=1)
    orders = ws_order.get_orders_between(start, end)
    orders_by_day = {}
    for row in orders:
        orders_by_day.setdefault(row.date.day, []).append({
            "user_id": row.user_id,
            "order_id": int(row.order),
            "comment": row.comment,
        })
    return jsonify({
        'orders_by_day': [{"day": k, "orders": v} for k, v in orders_by_day.items()],
    })


@app.post("/autifill")
def get_month_data():
    if not request.is_json:
        return {"error": "Request must be JSON"}, 415  # Unsupported Media Type
    form = request.get_json()
    user, error = _check_user(form, ws_permissions.Permission.MODIFY_ORDER)
    if error:
        return error
    try:
        date = ws_utils.parse_date(form['date'])
    except ValueError:
        return jsonify({"error": "Invalid json fields"}), 400  # Bad Request

    alg = work_scheduler.DistributionAlg(date)
    print(alg.start, alg.cur, alg.end)
    alg.prepare()
    alg.run()

    for day in ws_utils.daterange(alg.cur, alg.end):
        print(day)
        print(f'  all day {alg.make_all_day.get(day.day)}')
        for user in sorted(alg.make_work8h.get(day.day, []), key=lambda e: e[0].row.id):
            print(f'  work8h {user}')
        err = alg.error_all_day.get(day.day)
        if err:
            print(f'  err {err}')

    orders = ws_order.get_orders_between(alg.start, alg.end)
    orders_by_day = {}
    for row in orders:
        orders_by_day.setdefault(row.date.day, []).append({
            "user_id": row.user_id,
            "order_id": int(row.order),
            "comment": row.comment,
        })
    return jsonify({
        'orders_by_day': [{"day": k, "orders": v} for k, v in orders_by_day.items()],
    })


@app.post("/get_orders")
def get_orders():
    if not request.is_json:
        return {"error": "Request must be JSON"}, 415  # Unsupported Media Type
    form = request.get_json()
    user, error = _check_user(form, ws_permissions.Permission.QUERY_ORDER)
    if error:
        return error
    try:
        date = ws_utils.parse_date(form['date'])
    except ValueError:
        return jsonify({"error": "Invalid json fields"}), 400  # Bad Request
    orders = []
    for row in ws_order.get_orders(date):
        orders.append({
            "user_id": row.user_id,
            "order_id": int(row.order),
            "comment": row.comment,
        })
    return jsonify({
        'orders': orders,
    })


@app.post("/get_users")
def get_users():
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 415  # Unsupported Media Type
    form = request.get_json()
    user, error = _check_user(form, ws_permissions.Permission.QUERY_USER)
    if error:
        return error
    users = []
    for user in ws_user.get_users():
        users.append({
            'id': user.id,
            'login': user.login,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'fathers_name': user.fathers_name,
            'role': user.role.name.lower(),
        })
    return jsonify({
        'users': users,
    })


