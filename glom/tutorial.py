"""\

.. note::

   glom's tutorial is a runnable module, feel free to run ``pip
   install glom`` and ``from glom.tutorial import *`` in the Python
   REPL to glom along.

Dealing with Data
=================

Every application deals with data, and these days, even the simplest
applications deals with rich, heavily-nested data.

What does nested data looks like? In its most basic form::

  >>> data = {'a': {'b': {'c': 'd'}}}
  >>> data['a']['b']['c']
  'd'

Pretty simple right? On a good day, it certainly can be. But other
days, a value might not be set::

  >>> data2 = {'a': {'b': None}}
  >>> data2['a']['b']['c']
  Traceback (most recent call last):
  ...
  TypeError: 'NoneType' object is not subscriptable

Well that's no good. We didn't get our value. We got a TypeError, a
type of error that doesn't help us at all. The error message doesn't
even tell us which access failed. If ``data2`` had been passed to us,
we wouldn't know if ``'a'``, ``'b'``, or ``'c'`` had been set to
``None``.

If only there were a more semantically powerful accessor.

.. _access-granted:

Access Granted
==============

After years of research and countless iterations, the glom team landed
on this simple construct::

  >>> glom(data, 'a.b.c')
  'd'

Well that's short, and reads fine, but what about in the error case?

  >>> glom(data2, 'a.b.c')
  Traceback (most recent call last):
  ...
  PathAccessError: could not access 'c', index 2 in path Path('a', 'b', 'c'), got error: ...

That's more like it! We have a function that can give us our data, or
give us an error message we can read, understand, and act upon.

And would you believe this "deep access" example doesn't even scratch
the surface of the tip of the iceberg? Welcome to glom.

Point of Contact
================

glom is a practical tool for production use. To best demonstrate how
you can use it, we'll be building an API response. We're implementing
a Contacts web service, like an address book, but backed by an
ORM/database and compatible with web and mobile frontends.

Let's create a Contact to familiarize ourselves with our test data:

  >>> contact = Contact('Julian',
  ...                   emails=[Email(email='jlahey@svtp.info')],
  ...                   location='Canada')
  >>> contact.save()
  >>> contact.primary_email
  Email(id=5, email='jlahey@svtp.info', email_type='personal')
  >>> contact.add_date
  datetime.datetime(...)
  >>> contact.id
  5

As you can see, the Contact object has fields for ``primary_email``,
defaulting to the first email in the email list, and ``add_date``, to
track the date the contact was added. And as the unique,
autoincrementing ``id`` suggests, there appear to be a few other
contacts already in our system.

  >>> len(Contact.objects.all())
  5

Sure enough, we've got a little address book going here. But right now
it consists of plain Python objects, not very API friendly:

  >>> json.dumps(Contact.objects.all())
  Traceback (most recent call last):
  ...
  TypeError: Contact(id=1, name='Kurt', ...) ... is not JSON serializable

But at least we know our data, so let's get to building the API
response with glom.

First, let's set our source object, conventionally named *target*:

>>> target = Contact.objects.all()  # here we could do filtering, etc.

Next, let's specify the format of our result. Remember, the processing
is not happening here, this is just declaring the format. We'll be
going over the specifics of what each line does after we get our
results.

>>> spec = {'results': [{'id': 'id',
...                      'name': 'name',
...                      'add_date': ('add_date', str),
...                      'emails': ('emails', [{'id': 'id',
...                                             'email': 'email',
...                                             'type': 'email_type'}]),
...                      'primary_email': Coalesce('primary_email.email', default=None),
...                      'pref_name': Coalesce('pref_name', 'name', skip='', default=''),
...                      'detail': Coalesce('company',
...                                         'location',
...                                         ('add_date.year', str),
...                                         skip='', default='')}]}


With *target* and *spec* in hand, we're ready to glom, build our
response, and take a look the final json-serialized form:

>>> resp = glom(target, spec)
>>> print(json.dumps(resp, indent=2, sort_keys=True))
{
  "results": [
    {
      "add_date": "20...",
      "detail": "Mountain View",
      "emails": [
        {
          "email": "kurt@example.com",
          "id": 1,
          "type": "personal"
        }
      ],
      "id": 1,
      "name": "Kurt",
      "pref_name": "Kurt",
      "primary_email": "kurt@example.com"
    },
...
}

As we can see, our response looks a lot like our glom
specification. This type of WYSIWYG code is one of glom's most
important features. After we've appreciated that simple fact, let's
look at it line by line.

Understanding the Specification
===============================

For ``id`` and ``name``, we're just doing simple copy-overs. For
``add_date``, we use a tuple to denote repeated gloms; we access
``add_date`` and pass the result to ``str`` to convert it to a string.

For emails we need to serialize a list of subobjects. Good news, glom
subgloms just fine, too. We use a tuple to access ``emails``, iterate
over that list, and from each we copy over ``id`` and ``email``. Note
how ``email_type`` is easily remapped to simply ``type``.

For ``primary_email`` we see our first usage of glom's ``Coalesce``
feature. Much like SQL's keyword of the same name, ``Coalesce``
returns the result of the first spec that returns a valid value. In
our case, ``primary_email`` can be None, so a further access of
``primary_email.email`` would, outside of glom, result in an
AttributeError or TypeError like the one we described before the
Contact example. Inside of a glom ``Coalesce``, exceptions are caught
and we move on to the next spec. glom raises a ``CoalesceError`` when
no specs match, so we use ``default`` to tell it to return None
instead.

Some Contacts have nicknames or other names they prefer to go by, so
for ``pref_name``, we want to return the stored ``pref_name``, or fall
back to the normal name. Again, we use ``Coalesce``, but this time we
tell it not only to ignore the default ``GlomError`` exceptions, but
also ignore empty string values, and finally default to empty string
if all specs result in empty strings or :exc:`~glom.GlomError`.

And finally, for our last field, ``detail``, we want to conjure up a
bit of info that'll help jog the user's memory. We're going to include
the location, or company, or year the contact was added. You can see
an example of this feature as implemented by GitHub, here:
https://github.com/mahmoud/glom/stargazers

Conclusion
==========

We've seen a crash course in how glom can tame your data and act as a
powerful source of code coherency. glom transforms not only your data,
but also your code, bringing it in line with the data itself.

glom tamed our nested data, avoiding tedious, bug-prone lines,
replacing what would have been large sections with code that was
declarative, but flexible, an ideal balance for maintainability.

"""
import json
import datetime
from itertools import count
from collections import OrderedDict

import attr
from attr import Factory

from glom import glom, Coalesce

_email_autoincrement = lambda c=count(1): next(c)
_contact_autoincrement = lambda c=count(1): next(c)


def _default_email(contact):
    return contact.emails[0] if contact.emails else None


@attr.s
class ContactManager(object):
    """This type implements an oversimplified storage manager, wrapping an
    OrderedDict instead of a database. Those familiar with Django and
    SQLAlchemy will recognize the pattern being sketched here.
    """
    def all(self):
        return list(CONTACTS.values())

    def save(self, contact):
        CONTACTS[contact.id] = contact

    def get(self, contact_id):
        return CONTACTS.get(contact_id)



@attr.s
class Contact(object):
    id = attr.ib(Factory(_contact_autoincrement), init=False)
    name = attr.ib('')
    pref_name = attr.ib('')

    emails = attr.ib(Factory(list))
    primary_email = attr.ib(Factory(_default_email, takes_self=True))

    company = attr.ib('')
    location = attr.ib('')
    add_date = attr.ib(Factory(datetime.datetime.now))

    # The next two parts are part of the Django-esque Manager pattern,
    # mentioned in the ContactManager docstring
    objects = ContactManager()

    def save(self):
        self.objects.save(self)


@attr.s
class Email(object):
    id = attr.ib(Factory(_email_autoincrement), init=False)
    email = attr.ib('')
    email_type = attr.ib('personal')


CONTACTS = OrderedDict()
_add = ContactManager().save

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
