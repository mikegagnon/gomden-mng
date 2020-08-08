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

# Upon setting up the site, the first user to create an acccount is granted the
# ROOT and ADMIN roles
INSERT INTO roles (userid, role) VALUES (1, 'ROOT');
INSERT INTO roles (userid, role) VALUES (1, 'ADMIN');

COMMIT;