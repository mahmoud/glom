"""Every application deals with data, and these days, even the simplest
applications deals with rich, heavily-nested data.

What does nested data looks like? In its most basic form:

>>> data = {'a': {'b': {'c': 'd'}}}
>>> data['a']['b']['c']
'd'

Pretty simple right? On a good day, it certainly can be. But other
days, a value might not be set:

>>> data2 = {'a': {'b': None}}
>>> data2['a']['b']['c']
Traceback (most recent call last):
...
TypeError: 'NoneType' object is not subscriptable

Well that's no good. We didn't get our value, and the error message we
got was no help at all. The error doesn't even tell us which access
failed.

What we need is a more semantically powerful accessor. Something like:

>>> glom(data, 'a.b.c')
'd'
>>> glom(data2, 'a.b.c')
Traceback (most recent call last):
...
PathAccessError: could not access 'c' from path Path('a', 'b', 'c'), got error: 'NoneType' object has no attribute 'c'

And just like that, we have a function that can give us our data, or
give us an error message we can read, understand, and act upon. And
would you believe this "deep access" example doesn't even scratch
the surface of the tip of the iceberg? Welcome to glom.

"""
import datetime
from itertools import count

import attr
from attr import Factory

from glom import glom

_email_autoincrement = lambda c=count(1): next(c)
_contact_autoincrement = lambda c=count(1): next(c)


def _default_email(contact):
    return contact.emails[0] if contact.emails else None


@attr.s
class ContactManager(object):
    def all(self):
        return list(CONTACTS)


@attr.s
class Contact(object):
    id = attr.ib(Factory(_contact_autoincrement), init=False)
    name = attr.ib('')
    pref_name = attr.ib(None)

    emails = attr.ib(Factory(list))
    primary_email = attr.ib(Factory(_default_email, takes_self=True))

    company = attr.ib('')
    location = attr.ib('')
    add_date = attr.ib(datetime.datetime.now)

    objects = ContactManager()


@attr.s
class Email(object):
    id = attr.ib(Factory(_email_autoincrement), init=False)
    email = attr.ib('')
    email_type = attr.ib('personal')


CONTACTS = []
_add = CONTACTS.append

_add(Contact('Kurt',
             emails=[Email('kurt@example.com')],
             location='Mountain View'))

_add(Contact('Sean',
             emails=[Email('seanboy@example.com')],
             location='San Jose',
             company='D & D Mastering'))

_add(Contact('Matt',
             emails=[Email('mixtape@homemakelabs.com', email_type='work'),
                     Email('matt@example.com')],
             company='HomeMake Labs'))

_add(Contact('Julian', location='Sunnyvale Trailer Park'))

print(CONTACTS)
