from flask import Blueprint, render_template, request

from .db import Archive


archive = Blueprint("archive", __name__)


@archive.route("/all")
def list_all_page():
    page = request.args.get("page", 1, type=int)
    pagination = (Archive.query
                  .order_by(Archive.name.asc())
                  .paginate(page=page, per_page=8, error_out=False))
    return render_template("archive/list.html",
                           page=page,
                           items=pagination.items,
                           pagination=pagination)
