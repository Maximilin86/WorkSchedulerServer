import ws_db
import ws_user
import ws_session


def _db_test():
    ws_db.db_file.unlink()
    ws_db.initial()
    admin = ws_user.find_user_by_auth("admin", 'admin')
    token = ws_session.start_user_session(admin.id)

    session = ws_session.find_session_by_token(token)
    user = ws_user.get_user(session.user_id)
    print(user.first_name, user.last_name, user.role)


if __name__ == '__main__':
    _db_test()
