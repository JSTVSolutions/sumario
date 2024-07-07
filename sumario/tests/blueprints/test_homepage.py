# -*- coding: utf-8; mode: python -*-

from bs4 import BeautifulSoup as BS

from flask import url_for

from ..helpers import check_is_equal, with_tst_client, with_tst_request_context


@with_tst_request_context
@with_tst_client
def test_robots_txt(*args, **kwargs):
    test_client = kwargs["test_client"]

    response = test_client.get(url_for("sumario.robots_txt"))
    check_is_equal(response.status_code, 200)
    check_is_equal(response.headers["Content-Type"], "text/plain; charset=utf-8")


@with_tst_request_context
@with_tst_client
def test_homepage_is_en(*args, **kwargs):
    test_client = kwargs["test_client"]

    response = test_client.get(url_for("sumario.homepage"))
    check_is_equal(response.status_code, 200)
    check_is_equal(response.headers["Content-Type"], "text/html; charset=utf-8")
    bs = BS(response.data, "html5lib")
    check_is_equal(bs.find(id="hello").string.strip(), "Hello, World!")

    response = test_client.get("{}?hello={}".format(url_for("sumario.homepage"), "foo+bar"))
    check_is_equal(response.status_code, 200)
    check_is_equal(response.headers["Content-Type"], "text/html; charset=utf-8")
    bs = BS(response.data, "html5lib")
    check_is_equal(bs.find(id="hello").string.strip(), "Hello, Foo Bar!")


@with_tst_request_context
@with_tst_client
def test_homepage_is_es(*args, **kwargs):
    test_client = kwargs["test_client"]

    response = test_client.get(url_for("sumario.homepage"), headers={"Accept-Language": "es"})
    check_is_equal(response.status_code, 200)
    check_is_equal(response.headers["Content-Type"], "text/html; charset=utf-8")
    bs = BS(response.data, "html5lib")
    check_is_equal(bs.find(id="hello").string.strip(), "¡Hola, Mundo!")

    response = test_client.get(
        "{}?hello={}".format(url_for("sumario.homepage"), "foo+bar"), headers={"Accept-Language": "es"}
    )
    check_is_equal(response.status_code, 200)
    check_is_equal(response.headers["Content-Type"], "text/html; charset=utf-8")
    bs = BS(response.data, "html5lib")
    check_is_equal(bs.find(id="hello").string.strip(), "¡Hola, Foo Bar!")
