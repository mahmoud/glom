from collections import OrderedDict
from itertools import count

from glom import glom, tutorial
from glom.tutorial import Contact, Email

def test_tutorial_data():
    assert 4 <= len(tutorial.CONTACTS) < 10


def test_tutorial(monkeypatch):
    # Keep the tutorial doctest's sample database and ID counters unchanged.
    monkeypatch.setattr(tutorial, 'CONTACTS', OrderedDict())
    for increment in (tutorial._contact_autoincrement, tutorial._email_autoincrement):
        monkeypatch.setattr(increment, '__defaults__', (count(1),))

    target = {'a': {'b': {'c': 'd'}}}

    val = target['a']['b']['c']

    res = glom(target, 'a.b.c')

    assert res == val

    contact = Contact('Julian', emails=[Email('julian@sunnyvaletrailerpark.info')])
    contact.save()
    assert Contact.objects.get(contact_id=contact.id) is contact
