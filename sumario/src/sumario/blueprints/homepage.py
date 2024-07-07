# -*- coding: utf-8 -*-

from flask import Blueprint, request, render_template
from flask_babel import lazy_gettext as _

from ..components import users

homepage_blueprint = Blueprint("sumario", __name__)


@homepage_blueprint.route("/robots.txt")
def robots_txt():
    return render_template("sumario/robots.txt"), {"Content-Type": "text/plain; charset=utf-8"}


@homepage_blueprint.route("/")
def homepage():
    extra_context = {
        "register_form": users.RegisterFormClass(),
        "whom": request.args.get("hello", _("world")).title(),
    }
    return render_template("sumario/homepage.html", **extra_context)
