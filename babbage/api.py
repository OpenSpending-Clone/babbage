# Flask web api
# TODO: consider making this it's own Python package?
from datetime import date

from werkzeug.exceptions import NotFound
from flask import Blueprint, Response, request, current_app, json, url_for


blueprint = Blueprint('babbage_api', __name__)


def configure_api(app, manager):
    """ Configure the current Flask app with an instance of ``CubeManager`` that
    will be used to load and query data. """
    if not hasattr(app, 'extensions'):
        app.extensions = {}  # pragma: nocover
    app.extensions['babbage'] = manager


def get_manager():
    """ Try to locate a ``CubeManager`` on the Flask app which is currently
    processing a request. This will only work inside the request cycle. """
    return current_app.extensions['babbage']


def get_cube(name):
    """ Load the named cube from the current registered ``CubeManager``. """
    manager = get_manager()
    if not manager.has_cube(name):
        raise NotFound('No such cube: %r' % name)
    return manager.get_cube(name)


class JSONEncoder(json.JSONEncoder):
    """ This encoder will serialize all entities that have a to_dict
    method by calling that method and serializing the result. """

    def default(self, obj):
        if isinstance(obj, date):
            return obj.isoformat()
        if isinstance(obj, set):
            return [o for o in obj]
        if hasattr(obj, 'to_dict'):
            return obj.to_dict()
        return json.JSONEncoder.default(self, obj)


def jsonify(obj, status=200, headers=None):
    """ Custom JSONificaton to support obj.to_dict protocol. """
    data = JSONEncoder().encode(obj)
    if 'callback' in request.args:
        cb = request.args.get('callback')
        data = '%s && %s(%s)' % (cb, cb, data)
    return Response(data, headers=headers, status=status,
                    mimetype='application/json')


def url(*a, **kw):
    kw['_external'] = True
    return url_for(*a, **kw)


@blueprint.route('/')
def index():
    """ General system status report :) """
    from babbage import __version__
    return jsonify({
        'status': 'ok',
        'api': 'babbage',
        'cubes_index_url': url('babbage_api.cubes'),
        'version': __version__
    })


@blueprint.route('/cubes')
def cubes():
    """ Get a listing of all publicly available cubes. """
    cubes = []
    for cube in get_manager().list_cubes():
        cubes.append({
            'name': cube
        })
    return jsonify({
        'status': 'ok',
        'data': cubes
    })


@blueprint.route('/cubes/<name>/model')
def model(name):
    """ Get the model for the specified cube. """
    cube = get_cube(name)
    return jsonify({
        'status': 'ok',
        'name': name,
        'model': cube.model
    })
