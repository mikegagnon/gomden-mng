BEGIN TRANSACTION;

CREATE TABLE "users" (
    "userid" BIGSERIAL PRIMARY KEY,
    "username" TEXT,
    "displayname" TEXT,
    "email" TEXT,
    "password_hash" TEXT,
    "setup_state" TEXT, /* possible values: EMAIL_CONFIRMED, CONFIRMATION_EMAIL_SENT, tbd? */
    "ts" BIGINT DEFAULT CAST((extract(epoch from now()) * 1000) as BIGINT) /* num milliseconds since epoch */
);

CREATE TABLE "roles" (
    "roleid" BIGSERIAL PRIMARY KEY,
    "userid" BIGINT,
    "role" TEXT,
    "ts" BIGINT DEFAULT CAST((extract(epoch from now()) * 1000) as BIGINT) /* num milliseconds since epoch */
);

CREATE TABLE "usedtokens" (
    "usedtokenid" BIGSERIAL PRIMARY KEY,
    "token" TEXT,
    "ts" BIGINT DEFAULT CAST((extract(epoch from now()) * 1000) as BIGINT) /* num milliseconds since epoch */
);

CREATE TABLE "pages" (
    "pageid" BIGSERIAL PRIMARY KEY,
    "contributoruserid" BIGINT, /* the author of this revision */
    "pagename" TEXT,
    "revision" BIGINT, /* each version of a page gets its own row. revision # distinguishes between the various versoins */
    "content" TEXT,
    "ts" BIGINT DEFAULT CAST((extract(epoch from now()) * 1000) as BIGINT) /* num milliseconds since epoch */
);

/*
    Each record in captchas contains the text of a captcha that has been
    verified. This way, when a new captcha solution comes in, we can prevent
    replay attacks by making sure the captcha isn't in the database.
    Also, I'm going to write code to clean up old captchas so that they can
    be reused in the future.
*/
CREATE TABLE "captchas" (
    "captchaid" BIGSERIAL PRIMARY KEY,
    "ctext" TEXT,
    "ts" BIGINT DEFAULT CAST((extract(epoch from now()) * 1000) as BIGINT) /* num milliseconds since epoch */
);

CREATE TABLE "pagepermissions" (
    "pagepermissionid" BIGSERIAL PRIMARY KEY,
    "pagename" TEXT,
    "owneruserid" BIGINT,   /* the creator of the page */
    "allowcomments" BIGINT, /* 0 if not allowed; 1 if allowed */
    "allowedits" BIGINT,    /* 0 if not allowed; 1 if allowed */
    "ts" BIGINT DEFAULT CAST((extract(epoch from now()) * 1000) as BIGINT) /* num milliseconds since epoch */
);

/*
    Upon setting up the site, the first user to create an acccount is granted the
    ROOT and ADMIN roles
*/
INSERT INTO roles (userid, role) VALUES (1, '*ROOT*');
INSERT INTO roles (userid, role) VALUES (1, '*ADMIN*');

INSERT INTO pages (contributoruserid, pagename, revision, content)
VALUES (1, 'home', 1, 'Hello.');

INSERT INTO pagepermissions (pagename, owneruserid, allowcomments, allowedits)
VALUES ('home', 1, 1, 1);

COMMIT;