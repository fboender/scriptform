#!/bin/sh

HTPASSWD=htpasswd

err() {
    echo $* >&2
    exit 1
}

echo $username
echo $password1
echo $password2

if [ -z "$password1" ]; then
    err "Empty password specified"
fi
if [ "$password1" != "$password2" ]; then
    err "Passwords do not match."
fi

if [ $(egrep "^$username:" $HTPASSWD) ]; then
    UPDATE=1
else
    UPDATE=0
fi

htpasswd -s -b $HTPASSWD $username $password1 || exit $?

if [ "$UPDATE" -eq 1 ]; then
    echo "User password updated"
else
    echo "User created"
fi
