"""Nox sessions."""

import os
import shutil
import sys
from pathlib import Path
from typing import List
from uuid import uuid4

import nox


PACKAGE = "rfc_lookup"
PYTHON_VERSIONS = [
    "3.11",
    "3.10",
    "3.9",
    "3.8",
    "3.12",
]
PYTHON_VERSION_MAIN = PYTHON_VERSIONS[0]
LOCATIONS = ("src", "tests", "noxfile.py", "docs/conf.py")
nox.needs_version = ">= 2021.6.6"
nox.options.sessions = (
    "pre-commit",
    "safety",
    "mypy",
    "tests",
    "xdoctest",
    "docs-build",
)


def _uv_install(session: nox.Session, *args: str) -> None:
    """Install packages into the session using uv."""
    session.run(
        "uv",
        "pip",
        "install",
        "--python",
        session.virtualenv.location,
        *args,
        external=True,
    )


@nox.session(name="pre-commit", python=PYTHON_VERSION_MAIN)
def precommit(session: nox.Session) -> None:
    """Lint using pre-commit."""
    args: List[str] = session.posargs or [
        "run",
        "--all-files",
        "--hook-stage=manual",
    ]
    _uv_install(
        session,
        "black",
        "darglint",
        "flake8",
        "flake8-bandit",
        "flake8-bugbear",
        "flake8-docstrings",
        "flake8-rst-docstrings",
        "isort",
        "pep8-naming",
        "pre-commit",
        "pre-commit-hooks",
        "pyupgrade",
    )
    session.run("pre-commit", *args)


@nox.session(python=PYTHON_VERSION_MAIN)
def safety(session: nox.Session) -> None:
    """Scan dependencies for insecure packages."""
    _uv_install(session, "safety", ".")
    args = ["safety", "check", "--full-report"]

    if os.path.exists(".safety"):
        with open(".safety", encoding="utf-8") as f:
            lines = [line.strip() for line in f.readlines() if line.strip() != ""]
            if len(lines) > 0:
                vulns = ",".join(lines)
                args.append(f"--ignore={vulns}")

    session.run(*args)


@nox.session(python=PYTHON_VERSION_MAIN)
def mypy(session: nox.Session) -> None:
    """Type-check using mypy."""
    args: List[str] = session.posargs or list(
        filter(lambda a: a != "noxfile.py", LOCATIONS)
    )
    _uv_install(session, ".", "mypy", "pytest")
    session.run("mypy", *args)

    if not session.posargs and session.python == PYTHON_VERSION_MAIN:
        session.run("mypy", f"--python-executable={sys.executable}", "noxfile.py")


@nox.session(python=PYTHON_VERSIONS)
def tests(session: nox.Session) -> None:
    """Run the test suite."""
    _uv_install(
        session,
        ".",
        "coverage[toml]",
        "pytest",
        "pygments",
        "typing_extensions",
    )

    coverage_file = f".coverage.{session.python}.{uuid4().hex}"

    try:
        session.run(
            "coverage",
            "run",
            "--parallel",
            f"--data-file={coverage_file}",
            "-m",
            "pytest",
            *session.posargs,
        )
    finally:
        if session.interactive:
            session.notify("coverage", posargs=[])


@nox.session(python=PYTHON_VERSION_MAIN)
def coverage(session: nox.Session) -> None:
    """Produce the coverage report."""
    args: List[str] = session.posargs or ["report"]

    _uv_install(session, "coverage[toml]")

    if not session.posargs and any(Path().glob(".coverage.*")):
        session.run("coverage", "combine")

    session.run("coverage", *args)


@nox.session(python=PYTHON_VERSIONS)
def typeguard(session: nox.Session) -> None:
    """Runtime type checking using Typeguard."""
    _uv_install(session, ".", "pytest", "typeguard", "pygments")
    session.run("pytest", f"--typeguard-packages={PACKAGE}", *session.posargs)


@nox.session(python=PYTHON_VERSIONS)
def xdoctest(session: nox.Session) -> None:
    """Run examples with xdoctest."""
    if session.posargs:
        args: List[str] = [PACKAGE, *session.posargs]
    else:
        args = [f"--modname={PACKAGE}", "--command=all"]
        if "FORCE_COLOR" in os.environ:
            args.append("--colored=1")

    _uv_install(session, ".", "xdoctest[colors]")
    session.run("python", "-m", "xdoctest", *args)


@nox.session(name="docs-build", python=PYTHON_VERSION_MAIN)
def docs_build(session: nox.Session) -> None:
    """Build the documentation."""
    args: List[str] = session.posargs or ["docs", "docs/_build"]
    if not session.posargs and "FORCE_COLOR" in os.environ:
        args.insert(0, "--color")

    _uv_install(session, ".", "sphinx", "furo", "myst-parser")

    build_dir = Path("docs", "_build")
    if build_dir.exists():
        shutil.rmtree(build_dir)

    session.run("sphinx-build", *args)


@nox.session(python=PYTHON_VERSION_MAIN)
def docs(session: nox.Session) -> None:
    """Build and serve the documentation with live reloading on file changes."""
    args: List[str] = session.posargs or [
        "--open-browser",
        "docs",
        "docs/_build",
    ]
    _uv_install(session, ".", "sphinx", "sphinx-autobuild", "furo", "myst-parser")

    build_dir = Path("docs", "_build")
    if build_dir.exists():
        shutil.rmtree(build_dir)

    session.run("sphinx-autobuild", *args)
