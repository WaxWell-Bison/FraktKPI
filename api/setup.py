from setuptools import find_packages, setup

setup(
    name='flaskr',
    version='1.0.0',
    packages=find_packages(),
    install_requires=[
        'flask',
        'pymongo',
        'isodate'
    ],
)