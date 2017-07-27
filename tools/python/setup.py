from setuptools import setup
import boutiques

VERSION = boutiques.version

setup(name='boutiques',
      version=VERSION,
      description='Schema for describing commandlines',
      url='http://github.com/boutiques/boutiques',
      author='Tristan Glatard',
      author_email='tristan.glatard@gmail.com',
      license='MIT',
      packages=['boutiques'],
      include_package_data=True,
      install_requires=[
        'simplejson',
        'jsonschema',
      ],
      data_files=[('schema', ['boutiques/schema/boutiques.schema.json'])],
      zip_safe=False)
