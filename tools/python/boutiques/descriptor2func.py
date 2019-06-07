from boutiques.util.utils import loadJson
from boutiques import validate, execute, prettyprint
import json


def function(descriptor):
    '''
    Returns a function to invoke bosh.execute on a descriptor.
    args:
        descriptor: Zenodo id, file name, or JSON string representing a
                    descriptor.
        name: name of the function to create. Defaults to the tool name in the
              descriptor.
    '''

    validate(descriptor)
    descriptor_json = loadJson(descriptor)

    def f(*args, **kwargs):

        # Set default mode to 'launch'
        if len(args) > 0:
            mode = args[0]
        else:
            mode = 'launch'
        if mode not in ['launch', 'simulate']:
            mode = 'launch'
        else:
            args = args[1:]

        # Call bosh execute
        if mode == 'launch':
            return execute(mode, descriptor,
                           json.dumps(kwargs), *args)
        if len(kwargs) > 0:
            return execute(mode, descriptor,
                           '-i', json.dumps(kwargs), *args)
        return execute(mode, descriptor, *args)

    f.__name__ = str(descriptor_json['name'])

    # Documentation
    doc = []
    doc.append(r'''Runs {0} through its Boutiques interface.
    *args:
        - mode: 'launch' or 'simulate'. Defaults to 'launch'.
        - other arguments: will be passed to bosh execute. Examples: '-s',
          '-x'. See help(bosh.execute) for a complete list.
    *kwargs:
        {1} arguments as defined in the Boutiques descriptor, referenced
        from input ids. Example: {2}='some_value'. See complete
        list in descriptor help below.

'''.format(f.__name__, f.__name__, descriptor_json['inputs'][0]['id']))
    doc.append(prettyprint(descriptor))
    f.__doc__ = ''.join(doc)

    return f
