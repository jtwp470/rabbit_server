# rabbit_server

[![License](http://img.shields.io/badge/license-MIT-blue.svg?style=flat-square)]()
[![platform](https://img.shields.io/badge/platform-OS%20X%20%7C%20Linux-808080.svg?style=flat-square)]()

g0tiu5a CTF Scoreboard server.

*This application is under heavily development.* Please wait to use when the stable release.

## How to deploy & run

1. Fork this repository on your machine. `git clone https://github.com/jtwp470/rabbit_server.git`
2. Install below dependences:
    * Python (3.4 >=)
    * SQLite3
    * `pip install -r requirements.txt`
3. Initialize database. `python manage.py init_db`
4. Launch application `python manage.py runserver` when the apps launched, please access `http://localhost:5000/` at the default settings.
5. Create admin account. `http://localhost:5000/register`
6. Create new problem `http://localhost:5000/problem/new`
7. Enjoy!


## RECAPTCHA

セキュリティ向上のためユーザー登録をする際にreCAPTCHAを必要とするようにしました.そのためには`Public Key`と`Secret Key`を取得する必要があります.これらは[Googleのページ](https://www.google.com/recaptcha/admin)で取得し,設定する必要があります.設定ファイルは`config/localconfig.py`に書く必要があります.体裁は以下のとおりです.

```python
RECAPTCHA_PUBLIC_KEY = 'YOUR PUBLIC KEY'
RECAPTCHA_PRIVATE_KEY = 'YOUR SECRET KEY'
DEBUG = False # これも必要
```
