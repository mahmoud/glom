from glom import glom
from attr import dataclass
from typing import TYPE_CHECKING

if not TYPE_CHECKING:
    reveal_type = print


@dataclass
class Person(object):
    age: int

person = Person(age=25)
reveal_type(glom(person, 'age'))
