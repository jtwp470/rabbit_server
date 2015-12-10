from sqlalchemy.orm import synonym
from werkzeug import check_password_hash, generate_password_hash

from rabbit_server import db


class UserInfo(db.Model):
    """
    CRATE TABLE user_info (
        id primary_key unique integer,
        name text,
        mail text,
        hashed_password text,
        score integer
    )
    """
    __tablename__ = "user_info"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), default='', nullable=False)
    mail = db.Column(db.String(100), default='', nullable=False)
    score = db.Column(db.Integer, default=0)
    _password = db.Column('password', db.String(100), nullable=False)

    def _get_password(self):
        return self._password

    def _set_password(self, password):
        if password:
            password = password.strip()
        self._password = generate_password_hash(password)
    password_descriptor = property(_get_password, _set_password)
    password = synonym('_password', descriptor=password_descriptor)

    def check_password(self, password):
        password = password.strip()
        if not password:
            return False
        return check_password_hash(self.password, password)

    @classmethod
    def authenticate(cls, query, name, password):
        user = query(cls).filter(cls.name == name).first()
        if user is None:
            return None, False
        return user, user.check_password(password)

    def __repr__(self):
        return """
        <User id={id} name={name}
        mail={mail} score={score}
        """.format(id=str(self.id), name=self.name, mail=self.mail, score=str(self.score))


def init():
    db.create_all()
