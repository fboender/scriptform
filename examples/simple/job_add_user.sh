#!/bin/sh

HTACCESS=htaccess

err() {
    echo $* >&2
    exit 1
}

if [ -z "$password1" ]; then
    err "Empty password specified"
fi
if [ "$password1" != "$password2" ]; then
    err "Passwords do not match."
fi

if [ $(egrep "^$username:" $HTACCESS) ]; then
    UPDATE=1
else
    UPDATE=0
fi

htpasswd -s -b $HTACCESS $username $password1 || exit $?

if [ "$UPDATE" -eq 1 ]; then
    echo "User password updated"
else
    echo "User created"
fi
