
from rest_server import ws_server


if __name__ == '__main__':
    ws_server.app.run(host='0.0.0.0', port='8000', debug=True)
