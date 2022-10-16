import sqlalchemy
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, AnonymousUserMixin
from datetime import datetime
from itsdangerous import URLSafeTimedSerializer as Serializer
from itsdangerous.exc import BadData
from werkzeug.security import generate_password_hash, check_password_hash

from configure import conf

db = SQLAlchemy()


class Follow(db.Model):
    time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    follower_id = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True, nullable=True)
    followed_id = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True, nullable=True)
    follower = db.relationship("User", primaryjoin="Follow.follower_id==User.id", back_populates="follower")
    followed = db.relationship("User", primaryjoin="Follow.followed_id==User.id", back_populates="followed")



class AnonymousUser(AnonymousUserMixin):
    @property
    def email(self):
        return None


class User(db.Model, UserMixin):
    __tablename__ = "user"

    id = db.Column(db.Integer, autoincrement=True, primary_key=True, nullable=False)
    email = db.Column(db.String(32), nullable=False, unique=True)
    passwd_hash = db.Column(db.String(128), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey("role.id"), default=3)
    role = db.relationship("Role", back_populates="user")
    comment = db.relationship("Comment", back_populates="auth")

    follower = db.relationship("Follow", primaryjoin="Follow.follower_id==User.id", back_populates="follower",
                               lazy="dynamic")
    followed = db.relationship("Follow", primaryjoin="Follow.followed_id==User.id", back_populates="followed",
                               lazy="dynamic")

    @staticmethod
    def register_creat_token(email: str, passwd_hash: str):
        s = Serializer(conf["SECRET_KEY"])
        return s.dumps({"email": email, "passwd_hash": passwd_hash})

    @staticmethod
    def register_load_token(token: str):
        s = Serializer(conf["SECRET_KEY"])
        try:
            token = s.loads(token, max_age=3600)
            return token['email'], token['passwd_hash']
        except (BadData, KeyError):
            return None

    def login_creat_token(self, remember_me=False):
        s = Serializer(conf["SECRET_KEY"])
        return s.dumps({"email": self.email, "remember_me": remember_me})

    @staticmethod
    def login_load_token(token: str):
        s = Serializer(conf["SECRET_KEY"])
        try:
            token = s.loads(token, max_age=3600)
            return token['email'], token['remember_me']
        except (BadData, KeyError):
            return None

    @staticmethod
    def get_passwd_hash(passwd: str):
        return generate_password_hash(passwd)

    def check_passwd(self, passwd: str):
        return check_password_hash(self.passwd_hash, passwd)

    @property
    def passwd(self):
        return None

    @passwd.setter
    def passwd(self, passwd):
        self.passwd_hash = self.get_passwd_hash(passwd)


class Role(db.Model):
    __tablename__ = "role"

    USABLE = 1  # 账号可使用
    CHECK_COMMENT = 2
    CHECK_ARCHIVE = 4
    CHECK_FOLLOW = 8
    CREATE_COMMENT = 16
    CREATE_ARCHIVE = 32  # 系统权限
    FOLLOW = 64
    BLOCK_USER = 128  # 系统权限
    DELETE_COMMENT = 256  # 系统权限
    DELETE_ARCHIVE = 512  # 系统权限
    SYSTEM = 1024  # 系统权限

    id = db.Column(db.Integer, autoincrement=True, primary_key=True, nullable=False)
    name = db.Column(db.String(32), nullable=False, unique=True)
    permission = db.Column(db.Integer, nullable=False, default=95)  # 非系统权限
    user = db.relationship("User", back_populates="role")


    def has_permission(self, permission):
        return self.permission & permission == permission

    def add_permission(self, permission):
        if not self.has_permission(permission):
            self.permission += permission

    def remove_permission(self, permission):
        if self.has_permission(permission):
            self.permission -= permission


StudentClass = db.Table("archive_comment",
                        db.Column("archive_id", db.Integer, db.ForeignKey("archive.id"),
                                  nullable=False, primary_key=True),
                        db.Column("comment_id", db.Integer, db.ForeignKey("comment.id"),
                                  nullable=False, primary_key=True))


class Comment(db.Model):
    __tablename__ = "comment"

    id = db.Column(db.Integer, autoincrement=True, primary_key=True, nullable=False)
    title = db.Column(db.String(32), nullable=True)  # 允许为空
    content = db.Column(db.Text, nullable=False)
    create_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    update_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    auth_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    father_id = db.Column(db.Integer, db.ForeignKey("comment.id"))
    auth = db.relationship("User", back_populates="comment")
    father = db.relationship("Comment", foreign_keys="[Comment.father_id]", remote_side="[Comment.id]",
                             back_populates="son")
    son = db.relationship("Comment", foreign_keys="[Comment.father_id]", remote_side="[Comment.father_id]",
                          back_populates="father")
    archive = db.relationship("Archive", back_populates="comment", secondary="archive_comment")


class Archive(db.Model):
    __tablename__ = "archive"

    id = db.Column(db.Integer, autoincrement=True, primary_key=True, nullable=False)
    name = db.Column(db.String(32), nullable=False, unique=True)
    describe = db.Column(db.String(100), nullable=False)
    comment = db.relationship("Comment", back_populates="archive", secondary="archive_comment")


def create_all():
    try:
        db.create_all()
    except Exception:
        pass

    admin = Role(name="admin", permission=2047)
    coordinator = Role(name="coordinator", permission=1023)
    default = Role(name="default")

    db.session.add_all([admin, coordinator, default])
    db.session.commit()
