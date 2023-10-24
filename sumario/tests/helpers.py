# -*- coding: utf-8 -*-

import os

from datetime import datetime
from functools import partial, wraps

from flask import url_for as _url_for
from flask.testing import FlaskCliRunner

from flask_user.signals import user_registered

from sumario.app import run
from sumario.components import db, users
from sumario.models import Relay, User


def check_is_equal(n1, n2):
    assert n1 == n2, "{} (received) is not equal to {} (expected)".format(n1, n2)


def url_for(*args, **kwargs):
    kwargs["_external"] = True
    return _url_for(*args, **kwargs)


def login(test_client, test_user):
    login_data = {"email": test_user.email, "password": "password"}
    response = test_client.post(url_for("user.login"), follow_redirects=True, data=login_data)
    check_is_equal(response.status_code, 200)


def _post(fn):
    def wrapper(*args, **kwargs):
        headers = kwargs.setdefault("headers", {})
        headers["X-Forwarded-For"] = "127.0.0.1"
        return fn(*args, **kwargs)

    return wrapper


def _with_tst_request_context(create_app, fn):
    @wraps(fn)
    def test_with_tst_request_context_wrapper(*args, **kwargs):
        check_is_equal(os.environ["SUMARIO_ENVIRONMENT"], "testing")
        test_app = create_app(os.environ["SUMARIO_ENVIRONMENT"])

        rc = FlaskCliRunner(test_app).invoke(args=["delete-db"])
        assert rc.exit_code == 0
        rc = FlaskCliRunner(test_app).invoke(args=["create-db"])
        assert rc.exit_code == 0

        with test_app.test_request_context():
            kwargs["test_app"] = test_app
            rc = fn(*args, **kwargs)
        return rc

    return test_with_tst_request_context_wrapper


with_tst_request_context = partial(_with_tst_request_context, run)


def with_tst_user(fn):
    @wraps(fn)
    def test_with_test_user_wrapper(*args, **kwargs):
        test_app = kwargs["test_app"]
        test_user = User()
        test_user.email = "foobar@example.mil"
        test_user.password = users.hash_password("password")
        test_user.active = True
        test_user.email_confirmed_at = datetime.utcnow()
        db.session.add(test_user)
        db.session.commit()
        user_registered.send(test_app, user=test_user)
        kwargs["test_user"] = test_user
        rc = fn(*args, **kwargs)
        db.session.delete(test_user)
        db.session.commit()
        return rc

    return test_with_test_user_wrapper


def with_tst_client(fn):
    def test_with_test_client_wrapper(*args, **kwargs):
        test_app = kwargs["test_app"]
        with test_app.test_client() as test_client:
            test_client.post = _post(test_client.post)
            kwargs["test_client"] = test_client
            rc = fn(*args, **kwargs)
        return rc

    return test_with_test_client_wrapper


def with_tst_relay(fn):
    @wraps(fn)
    def test_with_test_relay_wrapper(*args, **kwargs):
        test_user = kwargs["test_user"]
        test_relay = Relay()
        test_relay.name = "Test Relay"
        test_relay.send_to = test_user.email
        test_relay.success_url = "/success"
        test_relay.user_uuid = test_user.uuid
        db.session.add(test_relay)
        db.session.commit()
        kwargs["test_relay"] = test_relay
        rc = fn(*args, **kwargs)
        db.session.delete(test_relay)
        db.session.commit()
        return rc

    return test_with_test_relay_wrapper
