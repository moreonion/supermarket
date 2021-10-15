from fixtures import import_example_data
from supermarket import App, model

app = App("supermarket")


@app.shell_context_processor
def _make_shell_context():
    # Add database and models to shell context
    env = {"app": app}
    env.update(model.__dict__)
    return env


# Custom commands


@app.cli.command()
def fixture_example_data():
    """Reset database and import example data from fixtures."""
    import_example_data()
