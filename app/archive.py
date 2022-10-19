from flask import Blueprint, render_template, request, url_for, redirect
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length, ValidationError
from flask_login import login_required

from .db import db, Archive, Role
from .login import role_required
from .logger import Logger


archive = Blueprint("archive", __name__)


class CreateArchiveForm(FlaskForm):
    name = StringField("名字", description="归档名字",
                       validators=[
                           DataRequired(f"必须填写归档名字"),
                           Length(1, 32, message=f"归档名字长度为0-32位")])
    describe = StringField("描述", description="归档描述",
                           validators=[
                               Length(0, 100, message=f"归档描述长度为0-100位")])
    submit = SubmitField("提交")

    def validate_name(self, field):
        """ 检验email是否合法 """
        if Archive.query.filter_by(name=field.data).first():
            raise ValidationError("归档已存在")


@archive.route("/all")
@role_required(Role.CHECK_ARCHIVE, "list all archive")
def list_all_page():
    page = request.args.get("page", 1, type=int)
    pagination = (Archive.query
                  .order_by(Archive.name.asc())
                  .paginate(page=page, per_page=8, error_out=False))
    Logger.print_load_page_log("list all archive")
    return render_template("archive/list.html",
                           page=page,
                           items=pagination.items,
                           pagination=pagination)



@archive.route("/create", methods=["GET", "POST"])
@login_required
@role_required(Role.CREATE_ARCHIVE, "create archive")
def create_page():
    form = CreateArchiveForm()
    if form.validate_on_submit():
        ac = Archive(name=form.name.data, describe=form.describe.data)
        db.session.add(ac)
        db.session.commit()
        Logger.print_user_opt_success_log(f"create new archive {ac.name}")
        return redirect(url_for("comment.list_all_page", archive=ac.id, page=1))
    Logger.print_load_page_log("create archive page")
    return render_template("archive/create.html", form=form)
