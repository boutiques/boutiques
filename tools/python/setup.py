from setuptools import setup
import boutiques

VERSION = boutiques.version

setup(name='boutiques',
      version=VERSION,
      description='Schema for describing bash command-line tools',
      url='http://github.com/boutiques/boutiques',
      author='Tristan Glatard, Gregory Kiar',
      author_email='tristan.glatard@gmail.com, gkiar07@gmail.com',
      license='MIT',
      packages=['boutiques'],
      include_package_data=True,
      install_requires=[
        'simplejson',
        'jsonschema',
      ],
      entry_points = {
        'console_scripts': [
            'bosh-validate=boutiques.validator:main',
            'bosh=boutiques.localExec:main',
            'bosh-invocation=boutiques.invocationSchemaHandler:main'
        ]
      },
      data_files=[('schema', ['boutiques/schema/descriptor.schema.json'])],
      zip_safe=False)
