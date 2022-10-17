from flask import Blueprint, render_template, request, abort

from .db import Comment


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
    pagination = (Comment.query
                  .filter(Comment.title != None).filter(Comment.father_id == None)
                  .order_by(Comment.create_time.desc(), Comment.title.desc())
                  .paginate(page=page, per_page=8, error_out=False))
    return render_template("comment/list.html",
                           page=page,
                           items=pagination.items,
                           pagination=pagination,
                           archive_name="全部讨论",
                           archive_describe="罗列了本站所有的讨论")
