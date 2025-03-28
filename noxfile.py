"""Nox sessions."""

import os
import shlex
import shutil
import sys
from pathlib import Path
from textwrap import dedent
from typing import List
from uuid import uuid4

import nox
from nox_poetry import Session, session


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


def activate_virtualenv_in_precommit_hooks(session: Session) -> None:
    """Activate virtualenv in hooks installed by pre-commit.

    This function patches git hooks installed by pre-commit to activate the
    session's virtual environment. This allows pre-commit to locate hooks in
    that environment when invoked from git.

    Args:
        session: The Session object.
    """
    assert session.bin is not None  # noqa: S101

    # Only patch hooks containing a reference to this session's bindir. Support
    # quoting rules for Python and bash, but strip the outermost quotes so we
    # can detect paths within the bindir, like <bindir>/python.
    bindirs = [
        bindir[1:-1] if bindir[0] in "'\"" else bindir
        for bindir in (repr(session.bin), shlex.quote(session.bin))
    ]

    virtualenv = session.env.get("VIRTUAL_ENV")
    if virtualenv is None:
        return

    headers = {
        # pre-commit < 2.16.0
        "python": f"""\
            import os
            os.environ["VIRTUAL_ENV"] = {virtualenv!r}
            os.environ["PATH"] = os.pathsep.join((
                {session.bin!r},
                os.environ.get("PATH", ""),
            ))
            """,
        # pre-commit >= 2.16.0
        "bash": f"""\
            VIRTUAL_ENV={shlex.quote(virtualenv)}
            PATH={shlex.quote(session.bin)}"{os.pathsep}$PATH"
            """,
        # pre-commit >= 2.17.0 on Windows forces sh shebang
        "/bin/sh": f"""\
            VIRTUAL_ENV={shlex.quote(virtualenv)}
            PATH={shlex.quote(session.bin)}"{os.pathsep}$PATH"
            """,
    }

    hookdir = Path(".git") / "hooks"
    if not hookdir.is_dir():
        return

    for hook in hookdir.iterdir():
        if hook.name.endswith(".sample") or not hook.is_file():
            continue

        if not hook.read_bytes().startswith(b"#!"):
            continue

        text = hook.read_text()

        if not any(
            Path("A") == Path("a")
            and bindir.lower() in text.lower()
            or bindir in text
            for bindir in bindirs
        ):
            continue

        lines = text.splitlines()

        for executable, header in headers.items():
            if executable in lines[0].lower():
                lines.insert(1, dedent(header))
                hook.write_text("\n".join(lines))
                break


@session(name="pre-commit", python=PYTHON_VERSION_MAIN)
def precommit(session: Session) -> None:
    """Lint using pre-commit."""
    args: List[str] = session.posargs or [
        "run",
        "--all-files",
        "--hook-stage=manual",
    ]
    session.install(
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

    try:
        session.run("poetry", "--version")
    except Exception:
        print("Installing poetry!")
        session.install("poetry")

    session.run("pre-commit", *args)
    if args and args[0] == "install":
        activate_virtualenv_in_precommit_hooks(session)


@session(python=PYTHON_VERSION_MAIN)
def safety(session: Session) -> None:
    """Scan dependencies for insecure packages."""
    requirements = session.poetry.export_requirements()

    session.install("safety")

    args = ["safety", "check", "--full-report", f"--file={requirements}"]

    if os.path.exists(".safety") is True:
        with open(".safety", encoding="utf-8") as f:
            lines = [
                line.strip() for line in f.readlines() if line.strip() != ""
            ]

            if len(lines) > 0:
                vulns = ",".join(lines)
                args.append(f"--ignore={vulns}")

    session.run(*args)


@session(python=PYTHON_VERSION_MAIN)
def mypy(session: Session) -> None:
    """Type-check using mypy."""
    args: List[str] = session.posargs or list(
        filter(lambda a: a != "noxfile.py", LOCATIONS)
    )

    session.install(".", "mypy", "pytest", "importlib-metadata")
    session.run("mypy", *args)

    if not session.posargs and session.python == PYTHON_VERSION_MAIN:
        session.run(
            "mypy", f"--python-executable={sys.executable}", "noxfile.py"
        )


@session(python=PYTHON_VERSIONS)
def pytype(session: Session) -> None:
    """Run the static type checker."""
    args: List[str] = session.posargs or ["--disable=import-error", *LOCATIONS]
    session.install("pytype")
    session.run("pytype", *args)


# @session
# @nox.parametrize(
#     "python,poetry",
#     [
#         (PYTHON_VERSIONS[0], "1.0.10"),
#         *((python, None) for python in PYTHON_VERSIONS),
#     ],
# )
# def tests(session: Session, poetry: str) -> None:
@session(python=PYTHON_VERSIONS)
def tests(session: Session) -> None:
    """Run the test suite."""
    session.install(".")
    session.install(
        "coverage[toml]",
        "poetry",
        "pytest",
        "pytest-datadir",
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


@session(python=PYTHON_VERSION_MAIN)
def coverage(session: Session) -> None:
    """Produce the coverage report."""
    args: List[str] = session.posargs or ["report"]

    session.install("coverage[toml]")

    if not session.posargs and any(Path().glob(".coverage.*")):
        session.run("coverage", "combine")

    session.run("coverage", *args)


@session(python=PYTHON_VERSIONS)
def typeguard(session: Session) -> None:
    """Runtime type checking using Typeguard."""
    session.install(".")
    session.install("pytest", "typeguard", "pygments")
    session.run("pytest", f"--typeguard-packages={PACKAGE}", *session.posargs)


@session(python=PYTHON_VERSIONS)
def xdoctest(session: Session) -> None:
    """Run examples with xdoctest."""
    if session.posargs:
        args: List[str] = [PACKAGE, *session.posargs]
    else:
        args = [f"--modname={PACKAGE}", "--command=all"]
        if "FORCE_COLOR" in os.environ:
            args.append("--colored=1")

    session.install(".")
    session.install("xdoctest[colors]")
    session.run("python", "-m", "xdoctest", *args)


@session(name="docs-build", python=PYTHON_VERSION_MAIN)
def docs_build(session: Session) -> None:
    """Build the documentation."""
    args: List[str] = session.posargs or ["docs", "docs/_build"]
    if not session.posargs and "FORCE_COLOR" in os.environ:
        args.insert(0, "--color")

    session.install(".")
    session.install("sphinx", "furo", "myst-parser")

    build_dir = Path("docs", "_build")
    if build_dir.exists():
        shutil.rmtree(build_dir)

    session.run("sphinx-build", *args)


@session(python=PYTHON_VERSION_MAIN)
def docs(session: Session) -> None:
    """Build and serve the documentation with live reloading on file changes."""
    args: List[str] = session.posargs or [
        "--open-browser",
        "docs",
        "docs/_build",
    ]
    session.install(".")
    session.install("sphinx", "sphinx-autobuild", "furo", "myst-parser")

    build_dir = Path("docs", "_build")
    if build_dir.exists():
        shutil.rmtree(build_dir)

    session.run("sphinx-autobuild", *args)
