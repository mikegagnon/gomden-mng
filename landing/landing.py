import flask
from flask import *
from flask_sslify import SSLify
from flask import Blueprint
from flask_wtf import FlaskForm

landing_blueprint = Blueprint('landing_blueprint', __name__, template_folder='templates', static_folder="static", static_url_path='/landing-static')

class EmptyForm(FlaskForm):
     pass

@landing_blueprint.route("/")
def landing():
    if "username" in session:
        form = EmptyForm()
        return render_template("new-landing.html", form=form)
    else:
        form = EmptyForm()
        return render_template("login.html", form=form)
