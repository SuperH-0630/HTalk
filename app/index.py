from flask import Blueprint, redirect, url_for, request

from .db import Comment


index = Blueprint("base", __name__)


@index.route("/")
def index_page():
    page = request.args.get("page", 1, type=int)
    return redirect(url_for("comment.list_all_page", page=page))
