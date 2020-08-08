# PUNT: better logging

import flask
from flask import *
from flask_wtf import FlaskForm
import json

from urllib.parse import unquote
import json
import cgi

import db
import config
from zabuton_log import *

send_email = None
def init(se):
    global send_email
    send_email = se

core_zabuton_blueprint = Blueprint('core_zabuton_blueprint', __name__, template_folder='templates', static_folder='static', static_url_path='/core-static')

class EmptyForm(FlaskForm):
    pass

