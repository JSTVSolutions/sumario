# -*- coding: utf-8 -*-

from .common import *  # noqa: F403


DEBUG = True
TESTING = True

SENTRY_ENVIRONMENT = "testing"

SERVER_NAME = "localhost:8443"

USER_PASSLIB_CRYPTCONTEXT_SCHEMES = ["plaintext"]

WTF_CSRF_ENABLED = False
