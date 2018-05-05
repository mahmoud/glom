
from glom.cli import main


def test_main_basic():
    argv = ['__', 'a.b.c', '{"a": {"b": "c"}}']
    assert main(argv) == 1

    argv = ['__', 'a.b.c', '{"a": {"b": {"c": "d"}}}']
    assert main(argv) == 0
