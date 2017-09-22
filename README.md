## Installation

Install the dependencies:

### Production

```bash
pip install -r requirements.txt
```

### Development

```bash
# Virtual env
cd supermarket
python3 -m venv env
source env/bin/activate

# Dependencies
sudo apt-get install postgresql libpq-dev
[env] pip install -r requirements/dev.txt

# Databases
createdb supermarket
createdb supermarket_test

# Fill database with example data
export FLASK_APP=api.py
flask fixture_example_data

# Interactive shell in app context
export FLASK_APP=api.py
flask shell
```

When using a virtual python environment, it's easiest to add
`export FLASK_APP=api.py` to the `activate` script.

Coding style should follow flake8 guidelines as configured in `.flake8` file.

## Run

For development you can use:

```bash
export FLASK_APP=api.py
flask run
```

For production you should use some real HTTP server like gunicorn or uWSGI.

## Tests

```bash
py.test
```
