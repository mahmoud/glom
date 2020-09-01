"""
slow gloms that came up organically, used as performance metrics
"""
import time

import attr

from glom import glom


def setup_list_of_dict(num=100):
    """
    a common use case is list-of-dicts object processing
    to prepare internal objects for JSON serialization
    """
    spec = [{
        'id': ('id', str),
        'name': 'short_name',
        'external_id': 'external_id',
        'created_date': 'created_date',
    }]

    Obj = attr.make_class(
        'Obj', ['id', 'short_name', 'external_id', 'created_date'])

    data = [
        Obj(i, 'name' + str(i), 'external' + str(i), 'now') for i in range(num)]

    return spec, data


def run(spec, data):
    start = time.time()
    glom(data, spec)
    end = time.time()
    print("{} us per object".format((end - start) / len(data) * 1e6))


if __name__ == "__main__":
    import cProfile
    spec, data = setup_list_of_dict(10000)
    cProfile.run('run(spec, data)')
