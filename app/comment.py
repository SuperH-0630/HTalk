from flask import Blueprint, render_template, request, abort

from .db import Comment, Archive, User


comment = Blueprint("comment", __name__)


@comment.route("/")
def comment_page():
    comment_id = request.args.get("comment_id", -1, type=int)
    if comment_id == -1:
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
    archive_id = request.args.get("archive", -1, type=int)

    if archive_id == -1:
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
    user_id = request.args.get("user", -1, type=int)
    if user_id == -1:
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
