import flask
from flask import session, Blueprint, request, render_template, abort, current_app, url_for, redirect
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from wtforms import StringField, PasswordField
from flask_bcrypt import Bcrypt
from itsdangerous import URLSafeTimedSerializer

from gomden_log import *
import config
import db
from config import STYLED_DOMAIN_NAME


bcrypt = None
send_email = None
CAPTCHA = None
def init(app, se, captcha):
    global send_email
    global bcrypt
    global CAPTCHA
    bcrypt = Bcrypt(app)
    send_email = se
    CAPTCHA = captcha

timedSerializer = URLSafeTimedSerializer(config.SECRET_KEY)

account_blueprint = Blueprint('account_blueprint', __name__, template_folder='templates', static_folder='static', static_url_path='/account-static')

class LogoutForm(FlaskForm):
     pass

class EmptyForm(FlaskForm):
    pass

class LoginForm(FlaskForm):
    usernameOrEmail = StringField("UsernameOrEmail")
    password = PasswordField("Password")

def pop_session():
    funcname = "pop_session()"
    debug(funcname, "popping session")
    session.pop("userid", None)
    session.pop("username", None)
    session.pop("displayname", None)
    session.pop("email", None)

class ForgotForm(FlaskForm):
    email = StringField("Email")

@account_blueprint.route("/forgot", methods=["GET", "POST"])
def forgot():
    funcname = "forgot()"

    form = ForgotForm(request.form)

    if request.method == "GET":
        debug(funcname, 'request.method == "GET"')
        return render_template("forgot-password.html", form=form, message=None)
    
    if not form.validate_on_submit():
        error(funcname, 'not form.validate_on_submit()')
        abort(403)

    email = form.email.data

    if not config.saneEmail(email):
        info(funcname, 'not saneEmail(email)')
        return render_template("message.html", form=form, message=config.FORGOT_PASSWORD_MESSAGE)

    user = db.getConfirmedUserByEmail(email)

    if not user:
        info(funcname, 'not user')
        return render_template("message.html", form=form, message=config.FORGOT_PASSWORD_MESSAGE)

    token = timedSerializer.dumps(email, salt="forgot-password")

    reset_url = url_for(
        "account_blueprint.reset_password",
        token=token,
        _external=True)

    subject = f"{STYLED_DOMAIN_NAME}: reset your password"
    sender = config.NOREPLY_EMAIL
    recipient = email
    body = (f"Follow this link to reset your password with {STYLED_DOMAIN_NAME}: " + reset_url)

    info(funcname, f"sending password-reset email to user")
    send_email.delay(subject, sender, recipient, body)

    return render_template("message.html", form=form, message=config.FORGOT_PASSWORD_MESSAGE)

class CreateAccountForm(FlaskForm):
    username = StringField("Username")
    displayname = StringField("DisplayName")
    email = StringField("Email")
    password1 = PasswordField("Password1")
    password2 = PasswordField("Password2")

def sendConfirmationEmail(username, email):
    # https://itsdangerous.palletsprojects.com/en/1.1.x/serializer/#the-salt
    token = timedSerializer.dumps([username, email], salt="email-account-confirmation")

    confirm_url = url_for(
        "account_blueprint.confirm_email",
        token=token,
        _external=True)

    subject = f"{STYLED_DOMAIN_NAME}: please confirm your email"
    sender = config.NOREPLY_EMAIL
    recipient = email
    body = ("Follow this link to confirm your new account with : " +
            confirm_url)

    send_email.delay(subject, sender, recipient, body)

def sendCannotCreateAccount(email):
    subject = f"{STYLED_DOMAIN_NAME}: Cannot create account"
    sender = config.NOREPLY_EMAIL
    recipient = email
    body = (f"You (or someone else), attempted to register a new account with your email address. Did you forget your username or password? If so, follow this link to reset your password for {STYLED_DOMAIN_NAME}: " + url_for("account_blueprint.forgot", _external=True))
    send_email.delay(subject, sender, recipient, body)

def sendNewRegisteredEmailToAdmin(username):
    subject = f"{STYLED_DOMAIN_NAME} new user registered"
    sender = config.NOREPLY_EMAIL
    recipient = config.ADMIN_EMAIL
    body = f"A new user registered: @{username}"
    send_email.delay(subject, sender, recipient, body)
    
class MyMultipleConfirmedAccounts(Exception):
    pass

def getConfirmedFromUsers(users):
    user = list(filter(lambda x: x["setup_state"] == "EMAIL_CONFIRMED", users))
    if len(user) == 1:
        return user[0]
    elif len(user) == 0:
        return None
    else:
        raise MyMultipleConfirmedAccounts

class ShouldNotContainConfirmedUser(Exception):
    pass

def getUnconfirmedUsersForMatchingEmailFromUsers(email, users):
    # Just to double check there's no confirmed users
    user = getConfirmedFromUsers(users)

    if user:
        raise ShouldNotContainConfirmedUser

    return list(filter(lambda x: x["email"] == email, users))

class MultipleUnconfirmedUsernamesForSameEmailAddress(Exception):
    pass

def getUnconfirmedUserByUsernameFromUsers(username, users):
    #Just to double check there's no confirmed users
    user = getConfirmedFromUsers(users)

    if user:
        raise ShouldNotContainConfirmedUser

    user = list(filter(lambda x: x["username"] == username, users))

    if len(user) == 1:
        return user[0]
    elif len(user) == 0:
        return None
    else:
        raise MultipleUnconfirmedUsernamesForSameEmailAddress

@account_blueprint.route("/create_account", methods=["GET", "POST"])
def create_account():
    funcname = "create_account()"

    form = CreateAccountForm(request.form)

    captcha = CAPTCHA.create()

    if "userid" in session:
        debug(funcname, 'Already logged in')
        return render_template("already_loggedin.html", form=form)

    if request.method == "GET":
        debug(funcname, 'request.method == "GET"')
        return render_template("create-account.html", captcha=captcha, form=form, message=None)
    
    if not form.validate_on_submit():
        error(funcname, 'not form.validate_on_submit()')
        abort(403)

    username = form.username.data.lower()
    displayname = config.trimDisplayName(form.displayname.data)
    email = form.email.data
    password1 = form.password1.data
    password2 = form.password2.data

    c_hash = request.form.get('captcha-hash')
    c_text = request.form.get('captcha-text')
    if not CAPTCHA.verify(c_text, c_hash):
        debug(funcname, 'bad captcha response')
        return render_template("create-account.html", captcha=captcha, form=form, message="I apologize, but your solution to the puzzle is not correct. I know this is annoying, but please try again.")
    
    if db.isCaptchaAlreadyUsed(c_text):
        # TODO: good error message
        print("replay")
        return render_template("create-account.html", captcha=captcha, form=form, message="I apologize, but your solution to the puzzle is odd. I know this is annoying, but please try again.")

    db.markCaptchaAsUsed(c_text)

    if not config.saneUsername(username):
        debug(funcname, 'not saneUsername(username)')
        return render_template("create-account.html", captcha=captcha, form=form, message="Invalid username.")

    if not config.saneDisplayName(displayname):
        debug(funcname, 'not saneDisplayName(displayname)')
        return render_template("create-account.html", captcha=captcha, form=form, message="Invalid display name.")

    if not config.saneEmail(email):
        debug(funcname, 'not saneEmail(email)')
        return render_template("create-account.html", captcha=captcha, form=form, message="Invalid email address.")

    if not config.sanePassword(password1) or not config.sanePassword(password2):
        debug(funcname, f"password(s) aren't sane")
        message = """
            Your password must be at least %d characters long
            """ % config.MIN_PASSWORD_LEN
        return render_template("create-account.html", captcha=captcha, form=form, message=message)

    if password1 != password2:
        debug(funcname, f"passwords don't match")
        message = "Your passwords do not match."
        return render_template("create-account.html", captcha=captcha, form=form, message=message)

    user = db.getConfirmedUserByUsername(username)
    if user:
        debug(funcname, "username already taken: %s" % username)
        message = "The username @" + username + " is already taken."
        return render_template("create-account.html", captcha=captcha, form=form, message=message)

    # We know: username is not taken

    # NOTE: there can be multiple __unconfirmed__ accounts with the same email
    # address, because someone who doesn't own the email might register accounts
    # for that email. However, there can only be one __confirmed__ account
    # per email address
    try:
        users = db.getAllUsersForAnySetupStateByEmail(email)
    except db.ShouldBeImposible:
        critcal(funcname, "Should be impossible from db.getAllUsersForAnySetupStateByEmail for email: %s" % email)
        abort(500)
    except db.MultipleConfirmedAccounts:
        critcal(funcname, "Multiple confirmed accounts for email in db: %s" % email)
        abort(500)

    try:
        confirmedUser = getConfirmedFromUsers(users)
    except MyMultipleConfirmedAccounts:
        critcal(funcname, "Multiple confirmed accounts for email: %s" % email)
        abort(500)

    # If this email already has a confirmed account, but it's different from
    # the username specified in the form
    if confirmedUser:
        # We know: username is not taken, but this email address is aleady confirmed
        bcrypt.generate_password_hash("prevent side channel")
        sendCannotCreateAccount(email)
        return render_template("create-account-success.html", captcha=captcha, form=form, email=email)

    # If this email address and username are neither confirmed
    else:
        # We know: username is not taken, and this email address is not confirmed
        try:
            usersWithEmail = getUnconfirmedUsersForMatchingEmailFromUsers(email, users)
        except ShouldNotContainConfirmedUser:
            bcrypt.generate_password_hash("prevent side channel")
            critcal(funcname, "ShouldNotContainConfirmedUser while calling getUnconfirmedUsersForMatchingEmailFromUsers")
            abort(500)
        
        try:
            user = getUnconfirmedUserByUsernameFromUsers(username, users)
        except MultipleUnconfirmedUsernamesForSameEmailAddress:
            bcrypt.generate_password_hash("prevent side channel")
            critcal(funcname, "MultipleUnconfirmedUsernamesForSameEmailAddress")
            abort(500)

        password_hash = bcrypt.generate_password_hash(password1).decode('utf-8')

        # If it's the case that that this email-username pair has an
        # unconfirmed account, then just re-send the confirmation email
        if user:
            # We know: username is not taken, and this email address is not confirmed,
            # and this username pair has already attempted account creation.
            # So, just re-send a confirmation email.
            bcrypt.generate_password_hash("prevent side channel")
            sendConfirmationEmail(username, email)

            return render_template("create-account-success.html", form=form, email=email)
        # If this email-username pair does not have a record in the database
        else:
            # We know: username is not taken, and this email address is not confirmed,
            # and we know this uername-email pair does not have a record in the db.
            # So, add a new record to the database
            password_hash = bcrypt.generate_password_hash(password1).decode('utf-8')
            db.createUnconfirmedAccount(username, displayname, email, password_hash)
            sendConfirmationEmail(username, email)

            return render_template("create-account-success.html", form=form, email=email)

@account_blueprint.route("/confirm-email/<token>", methods=["GET"])
def confirm_email(token):
    funcname = f'confirm_email(token)'

    form = EmptyForm(request.form)

    try:
        [username, email] = timedSerializer.loads(token, salt="email-account-confirmation", max_age=config.MAX_TOKEN_AGE)
    except:
        error(funcname, f"could not extract username, email from token. Abort 404")
        abort(404)

    user = db.getConfirmedUserByUsername(username)
    if user:
        # If the applicant has already registered this username/email pair
        if user["email"] == email:
            return render_template("message.html", form=form, message="You have already confirmed your account for username @%s." % username)
        # If someone else swooped in and registered this username
        else:
            return render_template("message.html", form=form, message="Sorry! Someone else registered the username @%s while we were waiting for you to click the confirmation link." % username)

    user = db.getUnconfirmedUserByUsernameEmail(username, email)
    if not user:
        critcal(funcname, "Could not find username-email pair: %s, %s" % (username, email))
        abort(500)

    try:
        db.confirmUsernameEmail(username, email)
    except db.ConfirmUsernameEmailErrorRowCountNotOne:
        critcal(funcname, "ConfirmUsernameEmailErrorRowCountNotOne")
        abort(500)

    session["userid"] = user["userid"]
    session["username"] = username
    session["displayname"] = user["displayname"]
    session["email"] = email

    info(funcname, f"sending email to admin")
    sendNewRegisteredEmailToAdmin(username)

    info(funcname, "success")
    return render_template("message.html", form=form, message="You have confirmed your account. You are now logged in.")

@account_blueprint.route("/logout", methods=["GET", "POST"])
def logout():
    funcname = "logout()"

    form = EmptyForm(request.form)

    if "userid" not in session:
        return render_template("message.html", form=form, message="You are already logged out.")

    if request.method == "GET":
        return render_template("logout.html", form=form)

    if not form.validate_on_submit():
        abort(403)

    pop_session()
    return render_template("message.html", form=form, message="You are now logged out.")

@account_blueprint.route("/login", methods=["GET", "POST"])
def login():
    funcname = "login()"

    form = LoginForm(request.form)

    if "userid" in session:
        debug(funcname, '"userid" in session')
        return render_template("already_loggedin.html", form=form)

    if request.method == "GET":
        debug(funcname, 'request.method == "GET"')
        return render_template("login.html", form=form, message=None)

    if not form.validate_on_submit():
        error(funcname, 'not form.validate_on_submit()')
        abort(403)

    usernameOrEmail = form.usernameOrEmail.data
    submitted_password = form.password.data

    if (not config.saneEmail(usernameOrEmail) and not config.saneUsername(usernameOrEmail)) or not config.sanePassword(submitted_password):
        info(funcname, "something isn't sane")
        bcrypt.check_password_hash(config.DUMMY_HASH, "foo")
        return render_template("login.html", form=form, message=config.BAD_PASSWORD_MESSAGE)

    user = db.getConfirmedUserByUsernameOrEmail(usernameOrEmail)

    if not user:
        info(funcname, "not user")
        bcrypt.check_password_hash(config.DUMMY_HASH, "foo")
        return render_template("login.html", form=form, message=config.BAD_PASSWORD_MESSAGE)

    if bcrypt.check_password_hash(user["password_hash"], submitted_password):
        session["userid"] = user["userid"]
        session["username"] = user["username"]
        session["displayname"] = user["displayname"]
        session["email"] = user["email"]
        debug(funcname, "success")

        return redirect(url_for("landing_blueprint.landing"))
    else:
        debug(funcname, "bad password")
        return render_template("login.html", form=form, message=config.BAD_PASSWORD_MESSAGE)

class ResetPasswordForm(FlaskForm):
    password1 = PasswordField("Password1")
    password2 = PasswordField("Password2")

@account_blueprint.route("/reset-password/<token>", methods=["GET"])
def reset_password(token):
    funcname = "reset_password(token)"

    try:
        email = timedSerializer.loads(token, salt="forgot-password", max_age=86400)
    except:
        error(funcname, f"could not extract email from token. Abort 404")
        abort(404)

    if db.hasTokenBeenUsed(token):
        debug(funcname, "token has already been used")
        form = ForgotForm()
        message = "Your forgot-password link has already been used. If you would like to reset your password again, please submit this form"
        return render_template("forgot-password.html", form=form, message=message)

    user = db.getConfirmedUserByEmail(email)

    # No sidechannel leak here because we have the assurance of the token
    if not user:
        critcal(funcname, f"user with email isn't in database")
        abort(404)

    form = ResetPasswordForm(request.form)

    # PUNT: is it secure to put the token in the form?
    return render_template("reset-password.html", email=email, form=form, token=token, message=None)

@account_blueprint.route("/do-password-reset/<token>", methods=["POST"])
def do_password_reset(token):
    funcname = "do_password_reset(token)"

    try:
        email = timedSerializer.loads(token, salt="forgot-password", max_age=config.MAX_TOKEN_AGE)
    except:
        error(funcname, f"could not extract email from token. Abort 404")
        abort(404)

    if db.hasTokenBeenUsed(token):
        debug(funcname, "token has already been used")
        form = ForgotForm()
        message = "Your forgot-password link has already been used. If you would like to reset your password again, please submit this form."
        return render_template("forgot-password.html", form=form, message=message)

    user = db.getConfirmedUserByEmail(email)

    # No sidechannel leak here because we have the assurance of the token
    if not user:
        critical(funcname, f"user with email isn't in database")
        abort(404)

    form = ResetPasswordForm(request.form)

    password1 = form.password1.data
    password2 = form.password2.data

    if not config.sanePassword(password1) or not config.sanePassword(password2):
        debug(funcname, f"password(s) aren't sane")
        return render_template("reset-password.html", email=email, form=form, token=token, message="Your password must be at least %d characters long." % config.MIN_PASSWORD_LEN)

    if password1 != password2:
        debug(funcname, f"passwords don't match")
        return render_template("reset-password.html", email=email, form=form, token=token, message="Your passwords do not match.")


    password_hash = bcrypt.generate_password_hash(password1).decode('utf-8')

    db.updateConfirmedPasswordByUsernameEmail(email, password_hash)

    session["userid"] = user["userid"]
    session["username"] = user["username"]
    session["displayname"] = user["displayname"]
    session["email"] = user["email"]

    db.markTokenUsed(token)

    return render_template("message.html", form=form, message="You have reset your password. You are now logged in.")

