import pytest

from glom import glom
from glom.matching import Match, M


def test():
	glom(1, Match(int))

