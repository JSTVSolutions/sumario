# -*- coding: utf-8 -*-

from flask_babel import lazy_gettext as _

import flask_user
from flask_user import UserManager

from wtforms import ValidationError

from .db import db
from ..models import User


class CustomUserManager(UserManager):
    def init_app(self, app):
        return super(CustomUserManager, self).init_app(app, db, User)

    def password_validator(self, form, field):
        minchars = 8
        if len(field.data) < minchars:
            raise ValidationError(
                _("Password must have at least {minchars} characters").format(minchars=minchars)
            )


users = CustomUserManager(None, db, User)


flask_user.translation_utils.init_translations = lambda *args, **kwargs: None
