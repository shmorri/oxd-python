"""
OxD Python
----------
Python bindings for Gluu OxD server.
"""
import codecs
import os
import re
from setuptools import setup


def find_version(*file_paths):
    here = os.path.abspath(os.path.dirname(__file__))
    with codecs.open(os.path.join(here, *file_paths), 'r') as f:
        version_file = f.read()
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


setup(
    name="oxdpython",
    version=find_version("oxdpython", "__init__.py"),
    url="https://github.com/GluuFederation/oxd-python",
    license="MIT",
    author="Gluu",
    author_email="info@gluu.org",
    description="Python binidings for Gluu OxD server",
    long_description="oxD Python is a client library for the Gluu oxD Server. For information about oxD, visit http://oxd.gluu.org",
    packages=["oxdpython"],
    zip_safe=False,
    install_requires=[],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX",
        "Operating System :: POSIX :: Linux",
        "Topic :: Internet",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Software Development",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
    ],
    include_package_data=True,
    entry_points={}
)
