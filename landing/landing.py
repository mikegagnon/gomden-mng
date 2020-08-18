import flask
from flask import *
from flask_sslify import SSLify
from flask import Blueprint
from flask_wtf import FlaskForm
import config
from config import STYLED_DOMAIN_NAME

landing_blueprint = Blueprint('landing_blueprint', __name__, template_folder='templates', static_folder="static", static_url_path='/landing-static')

class EmptyForm(FlaskForm):
     pass

@landing_blueprint.route("/")
def landing():
    form = EmptyForm()
    return render_template("wikipage.html", styled_domain_name=STYLED_DOMAIN_NAME, license=config.LICENSE, pagename="home", wikipage=True, form=form, revision=0)
