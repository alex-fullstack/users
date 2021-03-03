import os
from importlib.machinery import SourceFileLoader

from pkg_resources import parse_requirements
from setuptools import find_packages, setup


module_name = 'users'
module = SourceFileLoader(  # type: ignore
    module_name, os.path.join(module_name, '__init__.py')
).load_module()


def load_requirements(fname: str) -> list:
    requirements = []
    with open(fname, 'r') as fp:
        for req in parse_requirements(fp.read()):
            extras = f'[{",".join(req.extras)}]'if req.extras else ''
            requirements.append(f'{req.name}{extras}{req.specifier}')  # type: ignore
    return requirements


setup(
    name=module_name,
    platforms='all',
    python_requires=">3.5.*, <4",
    packages=find_packages(exclude=['tests']),
    install_requires=load_requirements('requirements.txt'),
    entry_points={
        'console_scripts': [
            '{0}-api = {0}.main:main'.format(module_name),
            '{0}-db = {0}.db:main'.format(module_name)
        ]
    },
    include_package_data=True
)