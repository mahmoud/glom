
from glom import glom, tutorial
from glom.tutorial import Contact, Email

def test_tutorial_data():
    assert len(tutorial.CONTACTS) == 4


def test_tutorial():
    target = {'a': {'b': {'c': 'd'}}}

    val = target['a']['b']['c']

    res = glom(target, 'a.b.c')

    assert res == val

    contact = Contact('Julian', emails=[Email('julian@sunnyvaletrailerpark.info')])
