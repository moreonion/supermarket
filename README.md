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

# Interactive shell in app context
python manager.py shell
```

## Run

For development you can use:

```bash
python manager.py runserver
```

For production you should use some real HTTP server like gunicorn or uWSGI.


## Tests

With server running:

```bash
py.test
```
