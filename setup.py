import os
import sys

import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="yangvoodoo",
    # CHANGE VERSION NUMBER HERE
    version="0.0.9.0",
    author="Adam Allen",
    author_email="allena29@users.noreply.github.com",
    description="Python based access to YANG Datatstores",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="http://github.com/allena29/python-yang-voodoo",
    packages=["yangvoodoo"],
    install_requires=[
        "cffi>=1.14.4",
        "Jinja2>=2.11.1",
        "dictdiffer>=0.8.1",
    ],
    zip_safe=False,
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache License 2.0",
        "Operating System :: OS Independent",
    ],
)
