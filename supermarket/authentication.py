import json
import urllib

from functools import wraps
from flask import current_app, request, _app_ctx_stack
from werkzeug.exceptions import BadRequest, Unauthorized, Forbidden
from jose import jwt


class Auth0(object):

    """Validate JSON Web Tokens against Auth0.

    Provides the following decorators to restrict access on views:
    @requires_auth              A valid token is required.
    @requires_scope(scope)      A valid token for the scope is required.

    """

    def __init__(self, app=None):
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        app.config.setdefault('AUTH0_DOMAIN', '')
        app.config.setdefault('AUTH0_API_AUDIENCE', '')
        app.config.setdefault('AUTH0_ALGORITHMS', ['RS256'])
        app.config.setdefault('AUTH0_ENABLE', app.config.get('TESTING', False))

    @property
    def enabled(self):
        return current_app.config['AUTH0_ENABLE']

    def get_token_auth_header(self):
        """Obtains the access token from the Authorization Header."""
        auth = request.headers.get('Authorization', None)
        if not auth:
            raise Unauthorized('Authorization header is expected.')

        parts = auth.split()

        if parts[0].lower() != 'bearer':
            raise Unauthorized('Authorization header must start with Bearer.')
        elif len(parts) == 1:
            raise Unauthorized('Token not found.')
        elif len(parts) > 2:
            raise Unauthorized('Authorization header must be Bearer token.')

        token = parts[1]
        return token

    def requires_auth(self, f):
        """Determines if the access token is valid."""
        @wraps(f)
        def decorated(*args, **kwargs):
            if self.enabled:
                token = self.get_token_auth_header()
                # get public key
                jsonurl = urllib.request.urlopen(
                    'https://{}/.well-known/jwks.json'.format(current_app.config['AUTH0_DOMAIN']))
                jwks = json.loads(jsonurl.read().decode())
                unverified_header = jwt.get_unverified_header(token)
                rsa_key = {}
                for key in jwks['keys']:
                    if key['kid'] == unverified_header['kid']:
                        rsa_key = {
                            'kty': key['kty'],
                            'kid': key['kid'],
                            'use': key['use'],
                            'n': key['n'],
                            'e': key['e']
                        }
                if not rsa_key:
                    raise BadRequest('Unable to find appropriate key.')
                try:
                    payload = jwt.decode(
                        token,
                        rsa_key,
                        algorithms=current_app.config['AUTH0_ALGORITHMS'],
                        audience=current_app.config['AUTH0_API_AUDIENCE'],
                        issuer='https://{}/'.format(current_app.config['AUTH0_DOMAIN'])
                    )
                except jwt.ExpiredSignatureError:
                    raise Unauthorized('Token is expired.')
                except jwt.JWTClaimsError:
                    raise Unauthorized('Incorrect claims, please check the audience and issuer.')
                except Exception:
                    raise BadRequest('Unable to parse authentication token.')

                _app_ctx_stack.top.current_user = payload

            return f(*args, **kwargs)

        return decorated

    def has_scope(self, required_scope):
        """Determines if the required scope is present in the access token.

        :param str required_scope    The scope required to access the resource.
        """
        if not self.enabled:
            return True
        token = self.get_token_auth_header()
        unverified_claims = jwt.get_unverified_claims(token)
        token_scopes = unverified_claims['scope'].split()
        for token_scope in token_scopes:
            if token_scope == required_scope:
                return True
        return False

    def requires_scope(self, required_scope):
        """Decorator to determine if the required scope is present in the access token."""
        def decorated(f):
            @wraps(f)
            def wrapper(*args, **kwargs):
                if not self.has_scope(required_scope):
                    raise Forbidden('Token is missing the required scope for this request.')
                return f(*args, **kwargs)
            return wrapper
        return decorated
