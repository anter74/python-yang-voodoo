import setuptools
with open('../README.md', 'r') as fh:
    long_description = fh.read()
setuptools.setup(name='yangvoodoo',
                 version='0.0.77', author='Adam Allen',
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
                 classifiers=['Programming Language :: Python :: 3',
                              'License :: OSI Approved :: Apache License 2.0',
                              'Operating System :: OS Independent'])
