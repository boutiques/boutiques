from boutiques.util.utils import loadJson
from boutiques import validate, execute, prettyprint
import json


def function(descriptor, name=None, mode='launch'):

    validate(descriptor)
    descriptor_json = loadJson(descriptor)

    def f(*args, **kwargs):
        if mode == 'launch':
            return execute(mode, descriptor,
                           json.dumps(kwargs), *args)
        elif mode == 'simulate':
            return execute(mode, descriptor,
                           '-i', json.dumps(kwargs), *args)
        else:
            raise Exception("Unsupported mode: {}".format(mode))

    if name is None:
        f.__name__ = str(descriptor_json['name'])
    else:
        f.__name__ = name
    f.__doc__ = prettyprint(descriptor)

    return f
