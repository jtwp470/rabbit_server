import os

# データベースの設定など
SQLALCHEMY_DATABASE_URI = "sqlite:///rabbit.db"
SECRET_KEY = os.urandom(24)
SQLALCHEMY_TRACK_MODIFICATIONS = True
