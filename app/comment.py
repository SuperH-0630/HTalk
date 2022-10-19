from flask import Blueprint, render_template, request, abort, flash, redirect, url_for
from flask_wtf import FlaskForm
from wtforms import TextAreaField, StringField, SelectMultipleField, SubmitField, ValidationError
from wtforms.validators import DataRequired, Length
from flask_login import current_user


from .db import db, Comment, Archive, User


comment = Blueprint("comment", __name__)


class WriteCommentForm(FlaskForm):
    title = StringField("标题", description="讨论标题", validators=[Length(0, 20, message="标题长度1-20个字符")])
    content = TextAreaField("内容", validators=[DataRequired(message="必须输入内容")])
    archive = SelectMultipleField("归档", coerce=int)
    submit = SubmitField("提交")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        archive = Archive.query.all()
        self.archive_res = []
        self.archive_choices = []
        for i in archive:
            self.archive_res.append(i.id)
            self.archive_choices.append((i.id, f"{i.name} ({i.comment_count})"))
        self.archive.choices = self.archive_choices

    def validate_archive(self, field):
        for i in field.data:
            if i not in self.archive_res:
                raise ValidationError("错误的归档被指定")


@comment.route("/")
def comment_page():
    comment_id = request.args.get("comment", None, type=int)
    if not comment_id:
        return abort(404)

    cm: Comment = Comment.query.filter_by(id=comment_id).first()
    if cm:
        return render_template("comment/comment.html",
                               comment=cm,
                               comment_son=cm.son)
    return abort(404)


@comment.route("/all")
def list_all_page():
    page = request.args.get("page", 1, type=int)
    archive_id = request.args.get("archive", None, type=int)

    if not archive_id == -1:
        pagination = (Comment.query
                      .filter(Comment.title != None).filter(Comment.father_id == None)
                      .order_by(Comment.create_time.desc(), Comment.title.desc())
                      .paginate(page=page, per_page=8, error_out=False))
        return render_template("comment/list.html",
                               page=page,
                               archive=archive_id,
                               items=pagination.items,
                               pagination=pagination,
                               archive_name="全部讨论",
                               archive_describe="罗列了本站所有的讨论",
                               title="主页")
    else:
        archive = Archive.query.filter_by(id=archive_id).first()
        if not archive:
            return abort(404)
        pagination = (archive.comment
                      .filter(Comment.title != None).filter(Comment.father_id == None)
                      .order_by(Comment.create_time.desc(), Comment.title.asc())
                      .paginate(page=page, per_page=8, error_out=False))
        return render_template("comment/list.html",
                               page=page,
                               archive=archive_id,
                               items=pagination.items,
                               pagination=pagination,
                               archive_name=archive.name,
                               archive_describe=archive.describe,
                               title=archive.name)


@comment.route("/user")
def user_page():
    page = request.args.get("page", 1, type=int)
    user_id = request.args.get("user", None, type=int)
    if not user_id:
        return abort(404)

    user: User = User.query.filter_by(id=user_id).first()
    if not user:
        return abort(404)

    pagination = (user.comment
                  .order_by(Comment.create_time.desc(), Comment.title.asc())
                  .paginate(page=page, per_page=8, error_out=False))
    return render_template("comment/user.html",
                           page=page,
                           user=user,
                           items=pagination.items,
                           pagination=pagination,
                           title=user.email)


@comment.route("/create", methods=["GET", "POST"])
def create_page():
    father_id = request.args.get("father", None, type=int)

    if father_id:
        father = Comment.query.filter_by(id=father_id).first()
        if not father:
            return abort(404)
    else:
        father = None

    form = WriteCommentForm()
    if form.validate_on_submit():
        title = form.title.data if len(form.title.data) > 0 else None
        archive_list = []
        for i in form.archive.data:
            archive = Archive.query.filter_by(id=i).first()
            if not archive:
                return abort(404)
            archive_list.append(archive)
        cm = Comment(title=title, content=form.content.data, father=father, archive=archive_list, auth=current_user)
        db.session.add(cm)
        db.session.commit()
        flash("讨论发表成功")
        return redirect(url_for("comment.comment_page", comment=cm.id))
    return render_template("comment/create.html", form=form, father=father)



