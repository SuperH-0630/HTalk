from flask import Blueprint, render_template, redirect, url_for, request, current_app, flash, abort
from flask_wtf import FlaskForm
from wtforms import (EmailField,
                     PasswordField,
                     BooleanField,
                     SubmitField,
                     ValidationError,
                     StringField)
from wtforms.validators import DataRequired, Length, Regexp, EqualTo
from flask_login import current_user, login_user, logout_user, login_required
from urllib.parse import urljoin
from sqlalchemy.exc import IntegrityError


from .db import db, User, Role, Follow
from .logger import Logger
from .mail import send_msg
from .login import role_required


auth = Blueprint("auth", __name__)


class AuthField(FlaskForm):
    @staticmethod
    def email_field(name: str, description: str):
        """ 提前定义 email 字段的生成函数，供下文调用 """
        return EmailField(name, description=description,
                          validators=[
                              DataRequired(f"必须填写{name}"),
                              Length(1, 32, message=f"{name}长度1-32个字符"),
                              Regexp(r"^[a-zA-Z0-9_\.\-]+@[a-zA-Z0-9_\-]+(\.[a-zA-Z0-9_\.]+)+$",
                                     message=f"{name}不满足正则表达式")])

    @staticmethod
    def passwd_field(name: str, description: str):
        """ 提前定义 passwd 字段的生成函数，供下文调用 """
        return PasswordField(name, description=description,
                             validators=[
                                 DataRequired(f"必须填写{name}"),
                                 Length(8, 32, message=f"{name}长度为8-32位")])

    @staticmethod
    def passwd_again_field(name: str, description: str, passwd: str = "passwd"):
        """ 提前定义 passwd again 字段的生成函数，供下文调用 """
        return PasswordField(f"重复{name}", description=description,
                             validators=[
                                 DataRequired(message=f"必须再次填写{name}"),
                                 EqualTo(passwd, message=f"两次输入的{name}不相同")])


class EmailPasswd(AuthField):
    email = AuthField.email_field("邮箱", "用户邮箱")
    passwd = AuthField.passwd_field("密码", "用户密码")


class PasswdLoginForm(EmailPasswd):
    remember = BooleanField("记住我")
    submit = SubmitField("登录")


class EmailLoginForm(AuthField):
    email = AuthField.email_field("邮箱", "用户邮箱")
    remember = BooleanField("记住我")
    submit = SubmitField("登录")


class RegisterForm(EmailPasswd):
    passwd_again = AuthField.passwd_again_field("密码", "用户密码")
    submit = SubmitField("注册")

    def validate_email(self, field):
        """ 检验email是否合法 """
        if User.query.filter_by(email=field.data).first():
            raise ValidationError("邮箱已被注册")


class ChangePasswdForm(AuthField):
    old_passwd = AuthField.passwd_field("旧密码", "用户原密码")
    passwd = AuthField.passwd_field("新密码", "用户新密码")
    passwd_again = AuthField.passwd_again_field("新密码", "用户新密码")
    submit = SubmitField("修改密码")

    def validate_passwd(self, field):
        """ 检验新旧密码是否相同 """
        if field.data == self.old_passwd.data:
            raise ValidationError("新旧密码不能相同")


class ChangeRoleForm(AuthField):
    email = AuthField.email_field("邮箱", "用户邮箱")
    role = StringField("角色", description="用户角色", validators=[DataRequired(message="必须指定用户角色")])
    submit = SubmitField("修改")

    def validate_role(self, field):
        if not Role.query.filter_by(name=field.data).first():
            raise ValidationError("角色不存在")


    def validate_email(self, field):
        if not User.query.filter_by(email=field.data).first():
            raise ValidationError("用户不存在")


def __load_login_page(passwd_login_form=None, email_login_form=None, register_form=None,
                      on_passwd_login=True, on_email_login=False, on_register=False):
    if not passwd_login_form:
        passwd_login_form = PasswdLoginForm()
    if not email_login_form:
        email_login_form = EmailLoginForm()
    if not register_form:
        register_form = RegisterForm()

    Logger.print_load_page_log("user login")
    return render_template("auth/login.html",
                           passwd_login_form=passwd_login_form,
                           email_login_form=email_login_form,
                           register_form=register_form,
                           on_passwd_login=on_passwd_login,
                           on_email_login=on_email_login,
                           on_register=on_register)


@auth.route("/")
def auth_page():
    if current_user.is_authenticated:  # 用户已经成功登陆
        return render_template("auth/yours.html")
    return __load_login_page()


@auth.route('/login/passwd', methods=["GET", "POST"])
def passwd_login_page():
    if current_user.is_authenticated:  # 用户已经成功登陆
        Logger.print_user_not_allow_opt_log("passwd-login")
        return redirect(url_for("auth.auth_page"))

    form = PasswdLoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_passwd(form.passwd.data) and user.role.has_permission(Role.USABLE):
            login_user(user, form.remember.data)
            next_page = request.args.get("next")
            if next_page is None or not next_page.startswith('/'):
                next_page = url_for('base.index_page')
            flash("登陆成功")
            Logger.print_user_opt_success_log(f"passwd login {form.email.data}")
            return redirect(next_page)
        flash("账号或密码错误")
        Logger.print_user_opt_fail_log(f"passwd login {form.email.data}")
        return redirect(url_for("auth.passwd_login_page"))
    return __load_login_page(passwd_login_form=form, on_passwd_login=True)


@auth.route('/login/email', methods=["GET", "POST"])
def email_login_page():
    if current_user.is_authenticated:  # 用户已经成功登陆
        Logger.print_user_not_allow_opt_log("email-login")
        return redirect(url_for("auth.auth_page"))

    form = EmailLoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.role.has_permission(Role.USABLE):
            token = user.login_creat_token(form.remember.data)
            login_url = urljoin(request.host_url, url_for("auth.email_login_confirm_page", token=token))
            send_msg("登录确认", user.email, "login", login_url=login_url)
            flash("登录确认邮件已发送至邮箱")
            Logger.print_user_opt_success_log(f"email login {form.email.data}")
            return redirect(url_for("base.index_page"))
        flash("账号不存在")
        Logger.print_user_opt_fail_log(f"email login {form.email.data}")
        return redirect(url_for("auth.passwd_login_page"))
    return __load_login_page(passwd_login_form=form, on_passwd_login=True)


@auth.route('/register', methods=["GET", "POST"])
def register_page():
    if current_user.is_authenticated:
        Logger.print_user_not_allow_opt_log("register")
        return redirect(url_for("auth.auth_page"))

    form = RegisterForm()
    if form.validate_on_submit():
        token = User.register_creat_token(form.email.data, form.passwd.data)
        register_url = urljoin(request.host_url, url_for("auth.register_confirm_page", token=token))
        send_msg("注册确认", form.email.data, "register", register_url=register_url)
        flash("注册提交成功, 请进入邮箱点击确认注册链接")
        Logger.print_import_user_opt_success_log(f"register {form.email.data}")
        return redirect(url_for("base.index_page"))
    return __load_login_page(register_form=form, on_register=True, on_passwd_login=False)


@auth.route('/confirm/register')
def register_confirm_page():
    token = request.args.get("token", None)
    if token is None:
        Logger.print_user_opt_fail_log(f"register confirm (bad token)")
        return abort(404)

    token = User.register_load_token(token)
    if token is None:
        Logger.print_user_opt_fail_log(f"register confirm (bad token)")
        return abort(404)

    if User.query.filter_by(email=token[0]).first():
        Logger.print_user_opt_fail_log(f"register confirm (bad token)")
        return abort(404)

    if User.query.limit(1).first():  # 不是第一个用户
        new_user = User(email=token[0], passwd_hash=User.get_passwd_hash(token[1]))
    else:
        admin = Role.query.filter_by(name="admin").first()
        if admin is None:
            Logger.print_sys_opt_fail_log(f"get admin(role)")
            return abort(500)
        new_user = User(email=token[0], passwd_hash=User.get_passwd_hash(token[1]), role=admin)
    db.session.add(new_user)
    db.session.commit()

    Logger.print_user_opt_success_log(f"register confirm {token[0]}")
    flash(f"用户{token[0]}认证完成")
    return redirect(url_for("base.index_page"))


@auth.route('/confirm/login')
def email_login_confirm_page():
    token = request.args.get("token", None)
    if token is None:
        Logger.print_user_opt_fail_log(f"login confirm (bad token)")
        return abort(404)

    token = User.login_load_token(token)
    if token is None:
        Logger.print_user_opt_fail_log(f"login confirm (bad token)")
        return abort(404)

    user = User.query.filter_by(email=token[0]).first()
    if not user:
        Logger.print_user_opt_fail_log(f"login confirm (bad token)")
        return abort(404)

    login_user(user, token[1])
    flash("登陆成功")
    Logger.print_user_opt_success_log(f"email login {user.email}")
    return redirect(url_for("base.index_page"))


@auth.route('/set/passwd', methods=['GET', 'POST'])
@login_required
def change_passwd_page():
    form = ChangePasswdForm()
    if form.validate_on_submit():
        if not current_user.check_passwd(form.old_passwd.data):
            Logger.print_user_opt_error_log(f"change passwd")
            flash("旧密码错误")
        else:
            current_user.passwd = form.passwd.data
            db.session.commit()

            Logger.print_user_opt_success_log(f"change passwd")
            flash("密码修改成功")
            logout_user()
            return redirect(url_for("auth.passwd_login_page"))
        return redirect(url_for("auth.change_passwd_page"))
    Logger.print_load_page_log("user change passwd")
    return render_template("auth/change_passwd.html", form=form)


@auth.route('/logout')
@login_required
def logout_page():
    logout_user()
    flash("退出登录成功")
    Logger.print_user_opt_success_log(f"logout")
    return redirect(url_for("base.index_page"))


@auth.route("/user")
def user_page():
    user_id = request.args.get("user", None, type=int)
    if not user_id:
        return abort(404)
    elif current_user.is_authenticated and current_user.id == user_id:
        return redirect(url_for("auth.auth_page"))
    user = User.query.filter_by(id=user_id).first()
    if not user:
        return abort(404)
    Logger.print_load_page_log(f"user {user.email} page")
    return render_template("auth/user.html", user=user)


@auth.route("/follower/list")
@login_required
@role_required(Role.CHECK_FOLLOW, "check follower")
def follower_page():
    if current_user.follower_count == 0:
        return render_template("auth/no_follow.html", title="粉丝", msg="你暂时一个粉丝都没有哦。")

    page = request.args.get("page", 1, type=int)
    pagination = current_user.follower.paginate(page=page, per_page=8, error_out=False)
    Logger.print_load_page_log(f"user {current_user.email} follower")
    return render_template("auth/follow.html",
                           items=[i.follower for i in pagination.items],
                           pagination=pagination,
                           title="粉丝")


@auth.route("/followed/list")
@login_required
@role_required(Role.CHECK_FOLLOW, "check followed")
def followed_page():
    if current_user.followed_count == 0:
        return render_template("auth/no_follow.html", title="关注", msg="你暂时未关注任何人。")

    page = request.args.get("page", 1, type=int)
    pagination = current_user.followed.paginate(page=page, per_page=8, error_out=False)
    Logger.print_load_page_log(f"user {current_user.email} followed")
    return render_template("auth/follow.html",
                           items=[i.followed for i in pagination.items],
                           pagination=pagination,
                           title="关注")


@auth.route("/followed/follow")
@login_required
@role_required(Role.FOLLOW, "follow")
def set_follow_page():
    user_id = request.args.get("user", None, type=int)
    if not user_id or user_id == current_user.id:
        return abort(404)

    user = User.query.filter_by(id=user_id).first()
    if not user:
        return abort(404)

    try:
        db.session.add(Follow(follower=current_user, followed=user))
        db.session.commit()
    except IntegrityError:
        flash("不能重复关注用户")
    else:
        flash("关注用户成功")

    return redirect(url_for("auth.user_page", user=user_id))


@auth.route("/followed/unfollow")
@login_required
@role_required(Role.FOLLOW, "unfollow")
def set_unfollow_page():
    user_id = request.args.get("user", None, type=int)
    if not user_id or user_id == current_user.id:
        return abort(404)

    user = User.query.filter_by(id=user_id).first()
    if not user:
        return abort(404)

    Follow.query.filter_by(follower=current_user, followed=user).delete()
    flash("取消关注用户成功")

    return redirect(url_for("auth.user_page", user=user_id))


@auth.route("/block")
@login_required
@role_required(Role.BLOCK_USER, "block user")
def set_block_page():
    user_id = request.args.get("user", None, type=int)
    if not user_id or user_id == current_user.id:
        return abort(404)

    user = User.query.filter_by(id=user_id).first()
    if not user:
        return abort(404)

    block = Role.query.filter_by(name="block").first()
    if not block:
        Logger.print_sys_opt_fail_log("get block(role)")
        return abort(500)

    user.role = block
    db.session.commit()

    return redirect(url_for("auth.user_page", user=user_id))


@auth.route('/role/user', methods=['GET', 'POST'])
@login_required
@role_required(Role.SYSTEM, "change user role")
def change_role_page():
    form = ChangeRoleForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if not user:
            flash("用户不存在")
            return redirect(url_for("auth.change_role_page"))

        role = Role.query.filter_by(name=form.role.data).first()
        if not role:
            flash("角色不存在")
            return redirect(url_for("auth.change_role_page"))

        user.role = role
        db.session.commit()
        flash("用户分组修改成功")
        Logger.print_sys_opt_success_log(f"move {user.email} to {role.name}")
        return redirect(url_for("auth.change_role_page"))
    Logger.print_load_page_log("change user role")
    return render_template("auth/change_role.html", form=form)
