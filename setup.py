from setuptools import setup

setup(
    name='argulib',
    version='0.1',
    packages=['test', 'argulib'],
    url='https://github.com/roman-kutlak/argulib',
    license='BSD',
    author='Roman Kutlak',
    author_email='kutlak.roman@gmail.com',
    description='A simple library for formal argumentation',
    install_requires=[
        'pyparsing'
    ],
)
