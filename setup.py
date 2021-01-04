from setuptools import setup, find_packages

setup(
    name='mygit',
    version='1.0',
    author='7Bpencil',
    author_email='efagot32@gmail.com',
    description='small git-clone vcs',
    entry_points={'console_scripts': ['mygit = mygit.main:main']},
    packages=find_packages()
)
