from setuptools import setup, find_packages

setup(
    name='mygit',
    version='6.66',
    author='7Bpencil',
    author_email='efagot32@gmail.com',
    description='small git-like vcs',
    entry_points={'console_scripts': ['mygit = mygit.main:start']},
    packages=find_packages()
)
