from flask_script import Command, Manager, Shell

import fixtures
from supermarket import App, model


def _make_context():
    env = {'app': app}
    env.update(model.__dict__)
    return env


app = App('supermarket')
manager = Manager(app)
manager.add_command("shell", Shell(make_context=_make_context))


class ExampleDataFixture(Command):
    """ Resets the database and adds the example data. """

    def run(self):
        fixtures.import_example_data()


manager.add_command('fixture-example-data', ExampleDataFixture())

if __name__ == '__main__':
    manager.run()
