## Installation

Install the dependencies:

### Production

```bash
pip install -r requirements.txt
```

### Development

```bash
# Virtual env
sudo pip install virtualenv
cd supermarket
virtualenv env
source env/bin/activate

# Dependencies
[env] pip install -r requirements/dev.txt

# Databases
sudo apt-get install postgresql
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

```bash
py.test
```
