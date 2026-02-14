# Contributing

When contributing to this repository, please first discuss the change you wish to make via issue,
email, or any other method with the owners of this repository before making a change.

Please note we have a code of conduct, please follow it in all your interactions with the project.

## Setting Up Your Development Environment

Follow these steps to get a local development environment ready for contributing.

### Prerequisites

- **Python >= 3.10**
- **Git** — [install instructions](https://git-scm.com/downloads)
- **pip** — ships with most Python distributions

### 1. Fork & Clone

```bash
git clone https://github.com/<YOUR-USERNAME>/boutiques.git
cd boutiques
```

### 2. Create a Virtual Environment

```bash
python -m venv .venv

# Linux / macOS
source .venv/bin/activate

# Windows (PowerShell)
.venv\Scripts\Activate.ps1
```

### 3. Install the Package with Dev Dependencies

The project defines a `dev` dependency group that includes testing tools (`pytest`, `pytest-cov`),
linting & formatting tools (`black`, `isort`, `flake8`, `codespell`, `pyupgrade`), `pre-commit`,
`coverage`, and `tox`.

```bash
pip install -e ".[dev]"
```

> **Note:** Runtime dependencies are installed automatically alongside the dev extras.
> If you also need the full optional runtime stack (e.g. `docopt`, `nexus-sdk`), install the `all` group instead:
> `pip install -e ".[dev,all]"`

### 4. Install Pre-commit Hooks

Pre-commit hooks run automatically on every commit to enforce consistent code style and catch
common issues **before** code reaches a pull request.

```bash
pre-commit install
```

You can also run all hooks against the entire codebase at any time:

```bash
pre-commit run --all-files
```

### 5. Run the Tests

```bash
pytest
```

To run a specific test file:

```bash
pytest boutiques/tests/test_<something>.py
```

To run tests with a coverage report:

```bash
coverage run --source boutiques -m pytest
coverage report -m
```

### 6. Linting & Formatting

The pre-commit hooks handle formatting and linting automatically on each commit. If you want to
run the individual tools manually:

| Tool | Command | Purpose |
|------|---------|---------|
| **black** | `black .` | Code formatting |
| **isort** | `isort .` | Import sorting |
| **flake8** | `flake8 boutiques docs` | PEP 8 compliance |
| **codespell** | `codespell` | Spelling checks |

> **Tip:** Running `pre-commit run --all-files` is the easiest way to apply all checks at once.

## Pull Request Process

1. Make tests for your code in `pytest`
2. Ensure pre-commit hooks pass — run `pre-commit run --all-files` before pushing.
3. Create a pull request against the `develop` branch.
  - Include evidence in your pull request of the functionality you added (i.e. show behaviour before and after changes were made, and demonstrate all unrelated content that has code touched by changes remains unchanged)
  - Try not to include too many features in one pull request. If multiple features were worked on, create a separate branch for each.
  - Mention the relevant issue number(s), if any.
4. Update relevant documentation with details of the changes
5. Get feedback from maintainers
6. Address suggested changes
7. Rinse & repeat until you and the maintainers agree

## Code of Conduct
> *"Just, don't be a jerk!"* :smile:

### Our Pledge

In the interest of fostering an open and welcoming environment, we as
contributors and maintainers pledge to making participation in our project and
our community a harassment-free experience for everyone, regardless of age, body
size, disability, ethnicity, gender identity and expression, level of experience,
nationality, personal appearance, race, religion, or sexual identity and
orientation.

### Our Standards

Examples of behavior that contributes to creating a positive environment
include:

* Using welcoming and inclusive language
* Being respectful of differing viewpoints and experiences
* Gracefully accepting constructive criticism
* Focusing on what is best for the community
* Showing empathy towards other community members

Examples of unacceptable behavior by participants include:

* The use of sexualized language or imagery and unwelcome sexual attention or
advances
* Trolling, insulting/derogatory comments, and personal or political attacks
* Public or private harassment
* Publishing others' private information, such as a physical or electronic
  address, without explicit permission
* Other conduct which could reasonably be considered inappropriate in a
  professional setting

### Our Responsibilities

Project maintainers are responsible for clarifying the standards of acceptable
behavior and are expected to take appropriate and fair corrective action in
response to any instances of unacceptable behavior.

Project maintainers have the right and responsibility to remove, edit, or
reject comments, commits, code, wiki edits, issues, and other contributions
that are not aligned to this Code of Conduct, or to ban temporarily or
permanently any contributor for other behaviors that they deem inappropriate,
threatening, offensive, or harmful.

### Scope

This Code of Conduct applies both within project spaces and in public spaces
when an individual is representing the project or its community. Examples of
representing a project or community include using an official project e-mail
address, posting via an official social media account, or acting as an appointed
representative at an online or offline event. Representation of a project may be
further defined and clarified by project maintainers.

### Enforcement

Instances of abusive, harassing, or otherwise unacceptable behavior may be
reported by contacting the project team on the Brainhack Slack (sign-up [here](https://brainhack-slack-invite.herokuapp.com/)).
All complaints will be reviewed and investigated and will result in a response that
is deemed necessary and appropriate to the circumstances. The project team is
obligated to maintain confidentiality with regard to the reporter of an incident.
Further details of specific enforcement policies may be posted separately.

Project maintainers who do not follow or enforce the Code of Conduct in good
faith may face temporary or permanent repercussions as determined by other
members of the project's leadership.

### Attribution

This Code of Conduct is adapted from the [Contributor Covenant][homepage], version 1.4,
available at [http://contributor-covenant.org/version/1/4][version]

[homepage]: http://contributor-covenant.org
[version]: http://contributor-covenant.org/version/1/4/
