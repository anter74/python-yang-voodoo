import os
import setuptools
with open('README.md', 'r') as fh:
    long_description = fh.read()

os.chdir('clients')
setuptools.setup(name='yangvoodoo',
                 version='0.0.3', author='Adam Allen',
                 author_email='allena29@users.noreply.github.com',
                 description='Python based access to YANG Datatstores',
                 long_description=long_description,
                 long_description_content_type='text/markdown',
                 url='http://github.com/allena29/pyyang-voodoo',
                 packages=['yangvoodoo'],
                 install_requires=[
                     'libyang',
                     'cffi',
                 ],
                 zip_safe=False,
                 include_package_data=True,

                 classifiers=['Programming Language :: Python :: 3',
                              'License :: OSI Approved :: Apache License 2.0',
                              'Operating System :: OS Independent'])