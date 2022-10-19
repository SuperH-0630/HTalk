from functools import wraps
from flask import abort
from flask_login import LoginManager, current_user
from .db import AnonymousUser, User, Role


login = LoginManager()
login.anonymous_user = AnonymousUser  # 设置未登录的匿名对象
login.login_view = "auth.passwd_login_page"


@login.user_loader
def user_loader(user_id: int):
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        return None
    if user.role.has_permission(Role.USABLE):
        return user
    return None


def role_required(role: int):
    def required(func):
        @wraps(func)
        def new_func(*args, **kwargs):
            if not current_user.role.has_permission(role):  # 检查相应的权限
                return abort(403)
            return func(*args, **kwargs)
        return new_func
    return required
