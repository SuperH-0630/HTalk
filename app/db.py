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
    follower_id = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True, nullable=True)  # 关注者
    followed_id = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True, nullable=True)  # 被关注者
    follower = db.relationship("User", primaryjoin="Follow.follower_id==User.id", back_populates="followed")
    followed = db.relationship("User", primaryjoin="Follow.followed_id==User.id", back_populates="follower")



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
    comment = db.relationship("Comment", back_populates="auth", lazy="dynamic")

    followed = db.relationship("Follow", primaryjoin="Follow.follower_id==User.id", back_populates="follower",
                               lazy="dynamic")  # User 关注的人
    follower = db.relationship("Follow", primaryjoin="Follow.followed_id==User.id", back_populates="followed",
                               lazy="dynamic")  # 关注 User 的人

    @property
    def comment_count(self):
        return self.comment.count()

    @property
    def follower_count(self):
        return self.follower.count()

    @property
    def followed_count(self):
        return self.followed.count()

    def in_followed(self, user):
        user_id = user.id
        if Follow.query.filter_by(followed_id=user_id, follower_id=self.id).first():
            return True
        return False


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


ArchiveComment = db.Table("archive_comment",
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
                          back_populates="father", lazy="dynamic")
    archive = db.relationship("Archive", back_populates="comment", secondary="archive_comment")


    @property
    def son_count(self):
        return self.son.count()


class Archive(db.Model):
    __tablename__ = "archive"

    id = db.Column(db.Integer, autoincrement=True, primary_key=True, nullable=False)
    name = db.Column(db.String(32), nullable=False, unique=True)
    describe = db.Column(db.String(100), nullable=False)
    comment = db.relationship("Comment", back_populates="archive", secondary="archive_comment", lazy="dynamic")

    @property
    def comment_count(self):
        return self.comment.filter(Comment.title != None).filter(Comment.father_id == None).count()


def create_all():
    try:
        db.create_all()
    except Exception:
        pass

    admin = Role(name="admin", permission=2047)
    coordinator = Role(name="coordinator", permission=1023)
    default = Role(name="default")
    block = Role(name="block", permission=0)

    db.session.add_all([admin, coordinator, default, block])
    db.session.commit()


def create_faker_user():
    from faker import Faker
    from sqlalchemy.exc import IntegrityError
    fake = Faker("zh_CN")

    count_user = 0
    while count_user < 100:
        user = User(email=fake.email(), passwd_hash=User.get_passwd_hash("passwd"), role_id=3)
        db.session.add(user)

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
        else:
            count_user += 1


def create_faker_comment(auth_max=100):
    from random import randint, random
    from faker import Faker
    from sqlalchemy.exc import IntegrityError
    fake = Faker("zh_CN")

    count_comment = 0
    while count_comment < 100:
        title = None
        if random() < 0.5:
            title = "加人" + fake.company()

        father = None
        if count_comment > 10 and random() < 0.5:
            father = randint(1, count_comment)

        time = fake.past_datetime()

        comment = Comment(title=title, content=fake.text(), update_time=time, create_time=time, father_id=father,
                          auth_id=randint(1, auth_max))
        db.session.add(comment)

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
        else:
            count_comment += 1


def create_faker_archive():
    from faker import Faker
    from sqlalchemy.exc import IntegrityError
    fake = Faker("zh_CN")

    count_archive = 0
    while count_archive < 20:
        company = fake.company()
        archive = Archive(name=company, describe=f"加人{company}")
        db.session.add(archive)

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
        else:
            count_archive += 1


def create_fake_archive_comment():
    from random import randint
    from sqlalchemy.exc import IntegrityError

    comment_count = Comment.query.count()
    archive_count = Archive.query.count()

    count_archive_comment = 0
    while count_archive_comment < 20:
        comment = Comment.query.offset(randint(0, comment_count)).limit(1).first()
        archive = Archive.query.offset(randint(0, archive_count)).limit(1).first()
        archive.archive.append(comment)

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
        else:
            count_archive_comment += 1


def create_fake_follow():
    from random import randint
    from sqlalchemy.exc import IntegrityError

    user_count = User.query.count()

    count_archive_comment = 0
    while count_archive_comment < 20:
        follower_id = randint(0, user_count)
        followed_id = randint(0, user_count)
        if follower_id == followed_id:
            continue

        follower = User.query.offset(follower_id).limit(1).first()
        followed = User.query.offset(followed_id).limit(1).first()
        follow = Follow(followed=followed, follower=follower)
        db.session.add(follow)

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
        else:
            count_archive_comment += 1
