from flask_cors import CORS
from moflask.flask import BaseApp

from .api import app as api_app
from .authentication import Auth0
from .model import db
from .schema import ma


class App(BaseApp):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        db.init_app(self)
        ma.init_app(self)
        CORS(allow_headers=["Authorization", "Content-Type"]).init_app(self)
        Auth0().init_app(self)
        self.register_blueprint(api_app, url_prefix="/api/v1")
