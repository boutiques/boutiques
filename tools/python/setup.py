from setuptools import setup

setup(name='boutiques',
      version='0.1',
      description='Schema for describing commandlines',
      url='http://github.com/boutiques/boutiques',
      author='Tristan Glatard',
      author_email='tristan.glatard@gmail.com',
      license='GPL',
      packages=['boutiques'],
      include_package_data=True,
      install_requires=[
        'simplejson',
        'jsonschema',
      ],
      data_files=[('schema', ['boutiques/schema/boutiques.schema.json'])],
      zip_safe=False)
