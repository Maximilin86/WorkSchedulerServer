import requests


WORK_SCHEDULER_URL = 'http://127.0.0.1:8000'


def is_json(r: requests.Response):
    mt = r.headers.get('Content-Type', '').split(';')[0]
    return (
            mt == "application/json"
            or mt.startswith("application/")
            and mt.endswith("+json")
    )


def rest_get(path):
    r = requests.get(WORK_SCHEDULER_URL + path)
    return r.json()


def rest_post(path, **data):
    r = requests.post(WORK_SCHEDULER_URL + path, json=data)
    if is_json(r):
        return r.json()
    else:
        return {'error': r.reason}


def main():
    for user in rest_get('/'):
        print(user)
    r = rest_post('/login', user='Test1', password='01234')
    if 'error' in r:
        print(r)
        return
    if 'token' not in r:
        print('user not found')
        return
    token = r['token']
    print(token)


if __name__ == '__main__':
    main()
