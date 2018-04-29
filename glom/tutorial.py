
import datetime
from itertools import count

import attr

_email_autoincrement = lambda c=count(1): next(c)
_contact_autoincrement = lambda c=count(1): next(c)


def _default_email(contact):
    return contact.emails[0] if contact.emails else None


@attr.s
class Contact(object):
    id = attr.ib(attr.Factory(_contact_autoincrement), init=False)
    name = attr.ib(str)
    pref_name = attr.ib(None)

    emails = attr.ib(list)
    primary_email = attr.ib(attr.Factory(_default_email, takes_self=True))

    company = attr.ib(str)
    location = attr.ib(str)
    add_date = attr.ib(datetime.datetime.now)


@attr.s
class Email(object):
    id = attr.ib(attr.Factory(_email_autoincrement), init=False)
    email = attr.ib(str)
    email_type = attr.ib('personal')


@attr.s
class ContactList(object):
    contacts = attr.ib()


@attr.s
class ModelQuerySet(object):
    def all(self):
        return ContactList(CONTACTS)


CONTACTS = []
_add = CONTACTS.append

_add(Contact('Kurt',
             emails=[Email('kurt@example.com')],
             location='Mountain View'))

print(CONTACTS)
