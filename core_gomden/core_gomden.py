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
import re

send_email = None
def init(se):
    global send_email
    send_email = se

core_gomden_blueprint = Blueprint('core_gomden_blueprint', __name__, template_folder='templates', static_folder='static', static_url_path='/core-static')

class EmptyForm(FlaskForm):
    pass

@core_gomden_blueprint.route("/page/<pagename>")
def viewPage(pagename):
    if not config.sanePagename(pagename):
        abort(404)

    form = EmptyForm()
    return render_template("wikipage.html", pagename=pagename, wikipage=True, form=form)

@core_gomden_blueprint.route("/get-page/<pagename>", methods=['GET'])
def getPage(pagename):
    if not config.sanePagename(pagename):
        abort(404)

    page = db.getPage(pagename)

    if not page:
        abort(404)

    pagePermissions = db.getPagePermissions(pagename)

    # TODO: logging
    if not pagePermissions:
        abort(500)

    pagenames = getLinkedPages(page)

    existingPagenames = db.getExistingPagenames(pagenames)

    result = {
        "page": page,
        "permissions": pagePermissions,
        "existingPagenames": existingPagenames,
    }

    return jsonify(result)

# Extracts all pagenames linked from content
def getLinkedPages(page):
    content = page["content"]
    matches = re.findall(r"page:([0-9a-z-]{3,100})", content)
    return matches

@core_gomden_blueprint.route("/save-comment/<pagename>", methods=['POST'])
def saveComment(pagename):
    if not config.sanePagename(pagename):
        abort(404)
    return jsonify({})

@core_gomden_blueprint.route("/edit/<pagename>", methods=['GET'])
def editPage(pagename):
    if not config.sanePagename(pagename):
        abort(404)

    form = EmptyForm()
    return render_template("edit-wikipage.html", pagename=pagename, wikipage=True, form=form)

def getUserOrAnonymousId():
    if "userid" in session:
        return session["userid"]
    else:
        return "0" # zero indicates anonymous user

def getUserOrAnonymousName():
    if "username" in session:
        return session["username"]
    else:
        return "Anonymous"

@core_gomden_blueprint.route("/save/<pagename>", methods=['POST'])
def savePage(pagename):
    if not config.sanePagename(pagename):
        abort(404)

    form = EmptyForm()
    # TODO: make robust
    newContent = request.form["textedit"]
    
    contributoruserid = getUserOrAnonymousId()

    db.savePage(contributoruserid, pagename, newContent)
    return redirect(url_for('core_gomden_blueprint.viewPage', pagename=pagename))


    #return render_template("edit-wikipage.html", pagename=pagename, wikipage=True, form=form)

@core_gomden_blueprint.route("/permissions/<pagename>", methods=['GET'])
def permissionsPage(pagename):
    if not config.sanePagename(pagename):
        abort(404)

    owner = db.getOwner(pagename)

    if owner == None:
        abort(404)

    userid = getUserOrAnonymousId()
    username = getUserOrAnonymousName()

    permissions = db.getPagePermissions(pagename)
    if permissions == None:
        abort(500)


    allowEdits = permissions["allowedits"]
    if allowEdits == 1:
        allowEdits = "true"
    else:
        allowEdits = "false"
        
    form = EmptyForm()
    return render_template("permissions-wikipage.html", allowEdits=allowEdits, userid=userid, username=username, ownerUserid=owner["userid"], ownerUsername=owner["username"], pagename=pagename, wikipage=True, form=form)
