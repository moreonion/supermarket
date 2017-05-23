from flask_script import Manager, Shell

from supermarket import App, model


def _make_context():
    env = {'app': app}
    env.update(model.__dict__)
    return env

app = App('supermarket')
manager = Manager(app)
manager.add_command("shell", Shell(make_context=_make_context))

if __name__ == '__main__':
    manager.run()
