from flask import Blueprint, render_template, redirect, url_for, request, current_app, flash, abort
from flask_wtf import FlaskForm
from wtforms import (EmailField,
                     PasswordField,
                     BooleanField,
                     SubmitField,
                     ValidationError)
from wtforms.validators import DataRequired, Length, Regexp, EqualTo
from flask_login import current_user, login_user, logout_user, login_required
from urllib.parse import urljoin


from .db import db, User, Role
from .logger import Logger
from .mail import send_msg


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


def __load_login_page(passwd_login_form=None, email_login_form=None, register_form=None,
                      on_passwd_login=True, on_email_login=False, on_register=False):
    if not passwd_login_form:
        passwd_login_form = PasswdLoginForm()
    if not email_login_form:
        email_login_form = EmailLoginForm()
    if not register_form:
        register_form = RegisterForm()

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
        Logger.print_user_not_allow_opt_log("passwd-login.txt")
        return redirect(url_for("auth.auth_page"))

    form = PasswdLoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_passwd(form.passwd.data):
            login_user(user, form.remember.data)
            next_page = request.args.get("next")
            if next_page is None or not next_page.startswith('/'):
                next_page = url_for('base.index_page')
            flash("登陆成功")
            Logger.print_user_opt_success_log(f"passwd login.txt {form.email.data}")
            return redirect(next_page)
        flash("账号或密码错误")
        Logger.print_user_opt_fail_log(f"passwd login.txt {form.email.data}")
        return redirect(url_for("auth.passwd_login_page"))
    return __load_login_page(passwd_login_form=form, on_passwd_login=True)


@auth.route('/login/email', methods=["GET", "POST"])
def email_login_page():
    if current_user.is_authenticated:  # 用户已经成功登陆
        Logger.print_user_not_allow_opt_log("email-login.txt")
        return redirect(url_for("auth.auth_page"))

    form = EmailLoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = user.login_creat_token(form.remember.data)
            login_url = urljoin(request.host_url, url_for("auth.email_login_confirm_page", token=token))
            send_msg("登录确认", user.email, "login", login_url=login_url)
            flash("登录确认邮件已发送至邮箱")
            Logger.print_user_opt_success_log(f"email login.txt {form.email.data}")
            return redirect(url_for("base.index_page"))
        flash("账号不存在")
        Logger.print_user_opt_fail_log(f"email login.txt {form.email.data}")
        return redirect(url_for("auth.passwd_login_page"))
    return __load_login_page(passwd_login_form=form, on_passwd_login=True)


@auth.route('/register', methods=["GET", "POST"])
def register_page():
    if current_user.is_authenticated:
        Logger.print_user_not_allow_opt_log("register.txt")
        return redirect(url_for("auth.auth_page"))

    form = RegisterForm()
    if form.validate_on_submit():
        token = User.register_creat_token(form.email.data, form.passwd.data)
        register_url = urljoin(request.host_url, url_for("auth.register_confirm_page", token=token))
        send_msg("注册确认", form.email.data, "register", register_url=register_url)
        flash("注册提交成功, 请进入邮箱点击确认注册链接")
        Logger.print_import_user_opt_success_log(f"register.txt {form.email.data}")
        return redirect(url_for("base.index_page"))
    return __load_login_page(register_form=form, on_register=True, on_passwd_login=False)


@auth.route('/confirm/register')
def register_confirm_page():
    token = request.args.get("token", None)
    if token is None:
        Logger.print_user_opt_fail_log(f"Confirm (bad token)")
        return abort(404)

    token = User.register_load_token(token)
    if token is None:
        Logger.print_user_opt_fail_log(f"Confirm (bad token)")
        return abort(404)

    if User.query.filter_by(email=token[0]).first():
        Logger.print_user_opt_fail_log(f"Confirm (bad token)")
        return abort(404)

    if User.query.limit(1).first():  # 不是第一个用户
        new_user = User(email=token[0], passwd_hash=User.get_passwd_hash(token[1]))
    else:
        admin = Role.query.filter_by(name="admin").first()
        if admin is None:
            Logger.print_user_opt_fail_log(f"Role admin not found")
            return abort(500)
        new_user = User(email=token[0], passwd_hash=User.get_passwd_hash(token[1]), role=admin)
    db.session.add(new_user)
    db.session.commit()

    Logger.print_import_user_opt_success_log(f"confirm {token[0]} success")
    flash(f"用户{token[0]}认证完成")
    return redirect(url_for("base.index_page"))


@auth.route('/confirm/login')
def email_login_confirm_page():
    token = request.args.get("token", None)
    if token is None:
        Logger.print_user_opt_fail_log(f"Confirm (bad token)")
        return abort(404)

    token = User.login_load_token(token)
    if token is None:
        Logger.print_user_opt_fail_log(f"Confirm (bad token)")
        return abort(404)

    user = User.query.filter_by(email=token[0]).first()
    if not user:
        Logger.print_user_opt_fail_log(f"Confirm (bad token)")
        return abort(404)

    login_user(user, token[1])
    flash("登陆成功")
    Logger.print_user_opt_success_log(f"passwd login.txt {user.email}")
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
    Logger.print_import_user_opt_success_log(f"logout")
    logout_user()
    flash("退出登录成功")
    return redirect(url_for("base.index_page"))

