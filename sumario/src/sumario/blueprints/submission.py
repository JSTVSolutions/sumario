# -*- coding: utf-8 -*-

import datetime
import re

from urllib.parse import urljoin, quote as urlquote, unquote as urlunquote

from flask import Blueprint, abort, redirect, render_template, request, url_for

import sqlalchemy

from ..components import db
from ..components.mail import send_message
from ..models import Relay, Submission

submission_blueprint = Blueprint("submission", __name__)


def render_text(**kwargs):
    return render_template("sumario/submission.txt", **kwargs)


def render_html(**kwargs):
    return render_template("sumario/submission.html", **kwargs)


def _build_url(request, url):
    referrer = request.referrer or ""
    return "{}?referrer={}".format(urljoin(referrer, url), urlquote(referrer))


def _user_has_credits(user):
    return user.credit_pool.num_credits > 0


def _has_whitespace(s):
    return bool(re.search(r"\s", s))


def _is_possible_bot(request):
    if not request.form:
        return True

    for k, v in request.form.items():
        name, *rest = k.split(":")

        if not name:
            return True

        if not rest:
            continue

        check_spam = rest[0] == "check-spam"

        if check_spam and not _has_whitespace(v):
            return True

    return False


@submission_blueprint.route("/<uuid>", methods=["GET", "POST"])
def submission(uuid):
    try:
        relay = db.session.get(Relay, uuid)
    except sqlalchemy.exc.StatementError:
        abort(404)

    if _is_possible_bot(request):
        return redirect(_build_url(request, url_for("submission.possiblebot")))

    if not _user_has_credits(relay.user):
        return redirect(_build_url(request, url_for("submission.nocredits")))

    new_submission = Submission()
    new_submission.client_addr = request.headers.getlist("X-Forwarded-For")[0]
    new_submission.relay_uuid = relay.uuid
    db.session.add(new_submission)

    credit_pool = relay.user.credit_pool
    # TODO: Prevent simultaneous updates. Lock reads.
    credit_pool.num_credits -= 1
    db.session.add(credit_pool)

    db.session.commit()

    extra_context = {
        "now": datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d %H:%M"),
        "form": request.form,
        "args": request.args,
    }

    send_message(relay.send_to, render_text(**extra_context), html=render_html(**extra_context))

    return redirect(_build_url(request, urljoin(request.url, relay.success_url)))


@submission_blueprint.route("/success", methods=["GET"])
def success():
    return render_template("sumario/success.html", referrer=urlunquote(request.args.get("referrer", "")))


@submission_blueprint.route("/nocredits", methods=["GET"])
def nocredits():
    return render_template("sumario/nocredits.html", referrer=urlunquote(request.args.get("referrer", "")))


@submission_blueprint.route("/possiblebot", methods=["GET"])
def possiblebot():
    return render_template("sumario/possiblebot.html", referrer=urlunquote(request.args.get("referrer", "")))
