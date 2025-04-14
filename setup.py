from setuptools import setup, find_packages

setup(
    name="kafka-test",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'kafka-python',
        'redis',
        'psycopg2-binary',
    ],
) 