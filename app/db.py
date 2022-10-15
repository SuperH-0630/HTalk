from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

if __name__ == '__main__':
    db.create_all()
