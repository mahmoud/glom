"""*glom gets results.*

To be more precise, glom helps pull together objects from other
objects in a declarative, dynamic, and downright simple way.

Built with services, APIs, and general serialization in mind, glom
helps filter objects as well as perform deep fetches which would be
tedious to perform in a procedural manner.

Where "schema" and other libraries focus on validation and parsing
less-structured data into Python objects, glom goes the other
direction, producing more-readily serializable data from valid
higher-level objects.

"""

_REGISTRY_MAP = {}
_REGISTRY_LIST = []  # TODO or some sort of tree


def register(target_type, accessor, iterate=False):
    if iterate is True:
        iterate = iter
    if iterate is not False and not callable(iterate):
        raise ValueError()

    if not callable(accessor):
        raise ValueError()

    _REGISTRY_MAP[target_type] = (accessor, iterate)
    _REGISTRY_LIST.append((accessor, iterate))

    return


def _get_path(target, remaining):
    pass


def glom(target, spec, ret=None):
    ret = {} if ret is None else ret

    for field, sub in spec.items():
        if isinstance(sub, str):
            sub = sub.split('.')
            cur, val = target, None
            for s in sub:
                val = _REGISTRY_MAP[type(cur)][0](cur, s)
                cur = val
            ret[field] = val

    return ret


# TODO: is it really necessary to register a "get_fields"
register(object, object.__getattribute__)
register(dict, dict.__getitem__)
register(list, list.__getitem__, True)  # TODO: are iterate and accessor mutually exclusive or?


def _main():
    val = {'a': {'b': 'c'},
           'd': {'e': ['f'],
                 'g': 'h'}}

    ret = glom(val, {'a': 'a.b',
                     'e': 'd.e'})  # d.e[0] or d.e: (callable to fetch 0)

    print(val)
    print(ret)
    return


if __name__ == '__main__':
    _main()

"""
TODO:

* More subspecs
  * dicts
  * lists (indicating iterability)
  * callables (for advanced processing)
* More supported target types
  * Django and SQLAlchemy Models and QuerySets
* Support for subclasses/superclasses via type tree

"""
