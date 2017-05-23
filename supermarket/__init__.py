from flask_cors import CORS
from moflask.flask import BaseApp

from .model import db


class App(BaseApp):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        db.init_app(self)
        CORS(allow_headers=['Authorization']).init_app(self)
