from flask_login import LoginManager
from .db import AnonymousUser, User


login = LoginManager()
login.anonymous_user = AnonymousUser  # 设置未登录的匿名对象
login.login_view = "auth.passwd_login_page"


@login.user_loader
def user_loader(user_id: int):
    return User.query.filter_by(id=user_id).first()
