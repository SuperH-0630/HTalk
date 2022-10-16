from flask import Blueprint, render_template, request

from .db import Comment
from datetime import datetime


comment = Blueprint("comment", __name__)


@comment.route("/all")
def list_all_page():
    page = request.args.get("page", 1, type=int)
    pagination = (Comment.query
                  .filter(Comment.title != None).filter(Comment.father_id == None)
                  .order_by(Comment.create_time.desc(), Comment.title.desc())
                  .paginate(page=page, per_page=20, error_out=False))
    return render_template("comment/list.html",
                           page=page,
                           items=pagination.items,
                           pagination=pagination)
