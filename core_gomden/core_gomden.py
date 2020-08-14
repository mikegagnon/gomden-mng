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
CAPTCHA = None
def init(se, captcha):
    global send_email
    global CAPTCHA
    send_email = se
    CAPTCHA = captcha

core_gomden_blueprint = Blueprint('core_gomden_blueprint', __name__, template_folder='templates', static_folder='static', static_url_path='/core-static')

class EmptyForm(FlaskForm):
    pass

@core_gomden_blueprint.route("/page/<pagename>/<revision>")
@core_gomden_blueprint.route("/page/<pagename>")
def viewPage(pagename, revision=None):
    if not config.sanePagename(pagename):
        abort(404)

    form = EmptyForm()
    if revision == None:
        revision = 0
    else:
        try:
            revision = int(revision)
        except:
            abort(404)

    return render_template("wikipage.html", license=config.LICENSE, pagename=pagename, wikipage=True, form=form, revision=revision)

@core_gomden_blueprint.route("/get-page/<pagename>/<revision>")
@core_gomden_blueprint.route("/get-page/<pagename>", methods=['GET'])
def getPage(pagename, revision=None):
    if not config.sanePagename(pagename):
        abort(404)

    page = db.getPage(pagename, revision)

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
    
    owner = db.getOwner(pagename)
    if owner == None:
        owner = {
            "userid": 0,
            "username": "Anonymous"
        }

    form = EmptyForm()
    captcha = CAPTCHA.create()
    #captchaHtml = CAPTCHA.captcha_html(captcha)
    captchaImg = captcha["img"]
    captchaHash = captcha["hash"]

    if "userid" in session:
        anonymous = "false"
    else:
        anonymous = "true"
        # Temporary hack: disable anonymous edits
        #return render_template("no-edit.html", anonymous=anonymous, captchaHash=captchaHash, captchaImg=captchaImg, editAgreement=config.EDIT_AGREEMENT, license=config.LICENSE, pagename=pagename, wikipage=True, form=form, allowEdit="false", ownerUsername=owner["username"])

    if hasPermissionToSavePage(pagename):
        return render_template("edit-wikipage.html", anonymous=anonymous, captchaHash=captchaHash, captchaImg=captchaImg, editAgreement=config.EDIT_AGREEMENT, license=config.LICENSE, pagename=pagename, wikipage=True, form=form, allowEdit="true", ownerUsername=owner["username"])
    else:
        return render_template("edit-wikipage.html", anonymous=anonymous, captchaHash=captchaHash, captchaImg=captchaImg, editAgreement=config.EDIT_AGREEMENT, license=config.LICENSE, pagename=pagename, wikipage=True, form=form, allowEdit="false", ownerUsername=owner["username"])

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

def hasPermissionToSavePage(pagename):

    permissions = db.getPagePermissions(pagename)

    # If the page does not exist, then let any user create the page
    if permissions == None:
        return True

    userid = getUserOrAnonymousId()

    # If the user is not anonymous AND the user is the owner
    if userid != 0 and permissions["owneruserid"] == userid:
        return True

    return permissions["allowedits"]

@core_gomden_blueprint.route("/checkCaptcha/<cHash>/<cText>", methods=['GET'])
def checkCaptcha(cHash, cText):
    if not CAPTCHA.verify(cText, cHash):
        abort(403)
    else:
        return "good"

@core_gomden_blueprint.route("/save/<pagename>", methods=['POST'])
def savePage(pagename):
    if not config.sanePagename(pagename):
        abort(404)

    if not hasPermissionToSavePage(pagename):
        abort(403)

    # If the user is anonymous, do captcha things
    userid = getUserOrAnonymousId()
    if userid == 0:
        c_hash = request.form.get('captcha-hash')
        c_text = request.form.get('captcha-text')
        if not CAPTCHA.verify(c_text, c_hash):
            # TODO: good error message
            print("bad hash")
            abort(403)

        if db.isCaptchaAlreadyUsed(c_text):
            # TODO: good error message
            print("replay")
            abort(403)

        db.markCaptchaAsUsed(c_text)

    form = EmptyForm()

    # TODO: make robust
    newContent = request.form["textedit"]

    if not config.saneContent(newContent):
        abort(403)
    
    contributoruserid = getUserOrAnonymousId()

    revision = db.savePage(contributoruserid, pagename, newContent)

    if config.ADMIN_SUBSCRIBE_ALL and contributoruserid != config.ADMIN_USER_ID:
        if revision == 1:
            subject = "page:%s new page: MichaelGagnon.wiki" % pagename
        else:
            subject = "page:%s new edit: MichaelGagnon.wiki" % pagename

        sender = config.NOREPLY_EMAIL
        recipient = config.ADMIN_EMAIL
        body = url_for('core_gomden_blueprint.viewPage', pagename=pagename, revision=revision, _external=True)
        send_email.delay(subject, sender, recipient, body)

    #send_email
    return redirect(url_for('core_gomden_blueprint.viewPage', pagename=pagename))

@core_gomden_blueprint.route("/save-permissions/<pagename>", methods=['POST'])
def savePermissions(pagename):
    if not config.sanePagename(pagename):
        abort(404)

    userid = getUserOrAnonymousId()

    # If anonymous
    if userid == 0:
        abort(403)

    owner = db.getOwner(pagename)
    if owner == None:
        abort(404)

    if owner["userid"] != userid:
        abort(403)

    form = EmptyForm()
    # TODO: make robust
    allowEdits = request.form.get('allowEdits')

    if allowEdits == "on":
        allowEdits = True
    else:
        allowEdits = False

    db.savePermissions(pagename, allowEdits)
    return redirect(url_for('core_gomden_blueprint.viewPage', pagename=pagename))

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
    return render_template("permissions-wikipage.html", license=config.LICENSE, allowEdits=allowEdits, userid=userid, username=username, ownerUserid=owner["userid"], ownerUsername=owner["username"], pagename=pagename, wikipage=True, form=form)

@core_gomden_blueprint.route("/history/<pagename>", methods=['GET'])
def historyPage(pagename):
    if not config.sanePagename(pagename):
        abort(404)

    history = json.dumps(db.getHistory(pagename))

    form = EmptyForm()
    return render_template("history-wikipage.html", license=config.LICENSE, pagename=pagename, wikipage=True, form=form, history=history)
