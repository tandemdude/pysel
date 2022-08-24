import os

import nox
from nox import options

PATH_TO_PROJECT = os.path.join(".", "pysel")
SCRIPT_PATHS = [
    PATH_TO_PROJECT,
    "noxfile.py",
]

options.sessions = ["format_fix", "mypy", "test"]


@nox.session()
def format_fix(session):
    session.install("-Ur", "dev_requirements.txt")
    session.run("python", "-m", "black", *SCRIPT_PATHS)
    session.run("python", "-m", "isort", *SCRIPT_PATHS)


@nox.session()
def format_check(session):
    session.install("-Ur", "dev_requirements.txt")
    session.run("python", "-m", "black", *SCRIPT_PATHS, "--check")


@nox.session()
def mypy(session):
    session.install("-Ur", "dev_requirements.txt")
    session.run("python", "-m", "mypy", "pysel")


@nox.session()
def test(session):
    session.install("-Ur", "dev_requirements.txt")
    session.run("python", "-m", "pytest", "tests")


# @nox.session(reuse_venv=True)
# def sphinx(session):
#     session.run("python", "-m", "sphinx.cmd.build", "docs/source", "docs/build", "-b", "html")
