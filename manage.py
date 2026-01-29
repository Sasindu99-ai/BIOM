from os import environ
from pathlib import Path

from env import env
from vvecon.zorion import App

env.init()
environ.setdefault('AUTH_ADMIN_URL', 'dashboard/auth')
environ.setdefault('AUTH_URL', 'auth')

app = App(Path(__file__).resolve().parent)
asgi = app.asgi()
wsgi = app.wsgi()

if __name__ == '__main__':
    app.run()
