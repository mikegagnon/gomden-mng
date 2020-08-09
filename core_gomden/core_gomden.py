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
from gomden_log import *

send_email = None
def init(se):
    global send_email
    send_email = se

core_gomden_blueprint = Blueprint('core_gomden_blueprint', __name__, template_folder='templates', static_folder='static', static_url_path='/core-static')

class EmptyForm(FlaskForm):
    pass

@core_gomden_blueprint.route("/view/<pagename>")
def viewPage(pagename):
    form = EmptyForm()
    return render_template("wikipage.html", pagename=pagename, wikipage=True, form=form)

@core_gomden_blueprint.route("/get-page/<pagename>", methods=['GET'])
def getPage(pagename):

    page = db.getPage(pagename)

    if not page:
        abort(404)

    pagePermissions = db.getPagePermissions(pagename)

    # TODO: logging
    if not pagePermissions:
        abort(500)

    result = {
        "page": page,
        "permissions": pagePermissions
    }

    return jsonify(result)


@core_gomden_blueprint.route("/save-comment/<pagename>", methods=['POST'])
def saveComment(pagename):
    return jsonify({})

@core_gomden_blueprint.route("/edit/<pagename>", methods=['GET'])
def editPage(pagename):
    form = EmptyForm()
    return render_template("edit-wikipage.html", pagename=pagename, wikipage=True, form=form)

@core_gomden_blueprint.route("/save/<pagename>", methods=['POST'])
def savePage(pagename):
    form = EmptyForm()
    return render_template("edit-wikipage.html", pagename=pagename, wikipage=True, form=form)
