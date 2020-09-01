"""
slow gloms that came up organically, used as performance metrics
"""
import time

import attr

from glom import glom, T



STR_SPEC = [{
    'id': ('id', str),
    'name': 'short_name',
    'external_id': 'external_id',
    'created_date': 'created_date',
}]


T_SPEC = [{
    'id': (T.id, str),
    'name': T.short_name,
    'external_id': T.external_id,
    'created_date': T.created_date,
}]


def setup_list_of_dict(num=100):
    """
    a common use case is list-of-dicts object processing
    to prepare internal objects for JSON serialization
    """
    Obj = attr.make_class(
        'Obj', ['id', 'short_name', 'external_id', 'created_date'])

    data = [
        Obj(i, 'name' + str(i), 'external' + str(i), 'now') for i in range(num)]

    return data


def run(spec, data):
    start = time.time()
    glom(data, spec)
    end = time.time()
    print("{} us per object".format((end - start) / len(data) * 1e6))


if __name__ == "__main__":
    import cProfile
    data = setup_list_of_dict(10000)
    cProfile.run('run(STR_SPEC, data)')
