## Installation

Install the dependencies:

### Production

```bash
pip install -r requirements.txt
```

### Development

```bash
pip install -r requirements/dev.txt
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

