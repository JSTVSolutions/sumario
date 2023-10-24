# -*- coding: utf-8 -*-

import datetime
import uuid

from flask_user import UserMixin

from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.event import listen
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import declarative_base

from sqlalchemy_utils.functions import create_database, database_exists, drop_database

from .components.db import db


ModelBase = declarative_base()
ModelBase.query = db.session.query_property()


class ImmutableError(Exception):
    pass


def _prevent_mutation(mapper, connection, target):
    raise ImmutableError("{} is immutable".format(target))


def pk(*args, **kwargs):
    kwargs["primary_key"] = True
    return db.Column(*args, **kwargs)


def optional(*args, **kwargs):
    kwargs["nullable"] = True
    return db.Column(*args, **kwargs)


def required(*args, **kwargs):
    kwargs["nullable"] = False
    return db.Column(*args, **kwargs)


def _relationship(*args, **kwargs):
    kwargs["cascade"] = "all,delete-orphan"
    return db.relationship(*args, **kwargs)


def has_many(*args, **kwargs):
    kwargs["lazy"] = "dynamic"
    return _relationship(*args, **kwargs)


def has_one(*args, **kwargs):
    kwargs["uselist"] = False
    return _relationship(*args, **kwargs)


def _default_uuid():
    return str(uuid.uuid4())


class ModelMixin(object):
    uuid = pk(UUID, default=_default_uuid)

    created_at = required(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = optional(db.DateTime, onupdate=datetime.datetime.utcnow)

    # TODO: JSONAPI requires each resource to contain an `id` serialized as a
    # string. Replace `uuid` with `id` in JSONAPI serializations.
    @hybrid_property
    def id(self):
        return self.uuid

    def __repr__(self):
        return "<{} {}>".format(self.__class__.__name__, self.uuid)

    def __str__(self):
        return str(self.uuid)


class Submission(ModelBase, ModelMixin):
    __tablename__ = "submission"

    client_addr = required(db.Unicode(255))
    relay_uuid = required(UUID, db.ForeignKey("relay.uuid"))


class Relay(ModelBase, ModelMixin):
    __tablename__ = "relay"

    deleted = required(db.Boolean, default=False)
    name = required(db.Unicode(255))
    send_to = required(db.Unicode(255))
    success_url = required(db.Unicode(255))
    user_uuid = required(UUID, db.ForeignKey("user.uuid"))

    submissions = has_many(Submission, backref=db.backref("relay"))


# TODO: listen(Relay, "before_delete", _prevent_mutation, raw=True)


class CreditPurchase(ModelBase, ModelMixin):
    __tablename__ = "credit_purchase"

    amount = required(db.Integer)
    credits_purchased = required(db.Integer, default=250)
    currency = required(db.Unicode(16))
    credit_pool_uuid = required(UUID, db.ForeignKey("credit_pool.uuid"))
    tx = required(db.Unicode)


listen(CreditPurchase, "before_update", _prevent_mutation, raw=True)


class CreditPool(ModelBase, ModelMixin):
    __tablename__ = "credit_pool"

    num_credits = required(db.Integer, default=0)
    user_uuid = required(UUID, db.ForeignKey("user.uuid"))

    credit_purchases = has_many(CreditPurchase, backref=db.backref("credit_pool"))


class User(ModelBase, ModelMixin, UserMixin):
    __tablename__ = "user"

    active = required(db.Boolean, default=False)
    email_confirmed_at = optional(db.DateTime)
    email = required(db.Unicode(255), unique=True)
    password = required(db.Unicode(255))

    credit_pool = has_one(CreditPool, backref=db.backref("user"))
    relays = has_many(Relay, backref=db.backref("user"))

    def __repr__(self):
        return "<{} {}>".format(self.__class__.__name__, self.email)

    def __str__(self):
        return self.email


def create_db(db, app):
    """Create database and tables in db for the current app.

    Args:
      db - An instance of `flask.ext.sqlalchemy.SQLAlchemy`.
      app - The current Flask app instance.

    """
    sqlalchemy_database_uri = app.config["SQLALCHEMY_DATABASE_URI"]

    if not database_exists(sqlalchemy_database_uri):
        create_database(sqlalchemy_database_uri)

    engine = create_engine(sqlalchemy_database_uri)

    with app.app_context():
        ModelBase.metadata.create_all(engine)


def delete_db(db, app):
    """Delete tables and database in db for the current app.

    Args:
      db - An instance of `flask.ext.sqlalchemy.SQLAlchemy`.
      app - The current Flask app instance.

    """
    sqlalchemy_database_uri = app.config["SQLALCHEMY_DATABASE_URI"]

    if database_exists(sqlalchemy_database_uri):
        drop_database(sqlalchemy_database_uri)
