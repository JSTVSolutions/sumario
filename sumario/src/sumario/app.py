# -*- coding: utf-8 -*-

import os

from flask import Flask

from werkzeug.middleware.proxy_fix import ProxyFix

from .callbacks import register_callbacks
from .components import babel, db, hashed_assets, mail, migrate, sentry, stripe, users
from .components.hashedassets import hash_assets
from .models import create_db, delete_db


_url_for = Flask.url_for


def url_for(*args, **kwargs):
    kwargs["_external"] = True
    return _url_for(*args, **kwargs)


Flask.url_for = url_for


def create_app(environment=os.environ["SUMARIO_ENVIRONMENT"]):
    app = Flask(__name__, static_folder="static/public", static_url_path="/static/")
    app.config.from_object("sumario.settings.{}".format(environment))

    app.url_map.strict_slashes = False
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_port=1, x_proto=1)

    @app.cli.command("hash-assets")
    def _hash_assets():
        hash_assets(app)

    @app.cli.command("create-db")
    def _create_db():
        """Create database and create all tables."""
        create_db(db, app)

    @app.cli.command("delete-db")
    def _delete_db():
        """Delete all tables and delete database."""
        delete_db(db, app)

    register_callbacks()

    return app


def _init_components(app):
    babel.init_app(app)
    db.init_app(app)
    hashed_assets.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    sentry.init_app(app)
    stripe.init_app(app)
    users.init_app(app)

    return app


def _register_blueprints(app):
    from .blueprints.homepage import homepage_blueprint

    app.register_blueprint(homepage_blueprint, url_prefix="/")

    from .blueprints.healthcheck import healthcheck_blueprint

    app.register_blueprint(healthcheck_blueprint, url_prefix="/healthcheck")

    from .blueprints.help import help_blueprint

    app.register_blueprint(help_blueprint, url_prefix="/help")

    from .blueprints.dashboard import dashboard_blueprint

    app.register_blueprint(dashboard_blueprint, url_prefix="/dashboard")

    from .blueprints.account import account_blueprint

    app.register_blueprint(account_blueprint, url_prefix="/account")

    from .blueprints.submission import submission_blueprint

    app.register_blueprint(submission_blueprint, url_prefix="/submission")

    return app


def run(*args, **kwargs):
    app = _register_blueprints(_init_components(create_app(*args, **kwargs)))

    create_db(db, app)

    return app
