from flask import Blueprint, render_template


index = Blueprint("base", __name__)


@index.route("/")
def index_page():
    return render_template("index/index.html")
