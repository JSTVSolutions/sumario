# -*- coding: utf-8 -*-

from flask_user.signals import user_registered

from .components import db
from .models import CreditPool, CreditPurchase


def _on_user_registered(app, user, **kwargs):
    new_credit_pool = CreditPool()
    new_credit_pool.user_uuid = user.uuid
    new_credit_pool.num_credits = 25
    db.session.add(new_credit_pool)
    db.session.commit()

    new_credit_purchase = CreditPurchase()
    new_credit_purchase.amount = 0
    new_credit_purchase.credits_purchased = user.credit_pool.num_credits
    new_credit_purchase.currency = "FREE!"
    new_credit_purchase.credit_pool_uuid = user.credit_pool.uuid
    new_credit_purchase.tx = 0
    db.session.add(new_credit_purchase)
    db.session.commit()


def register_callbacks():
    user_registered.connect(_on_user_registered)
