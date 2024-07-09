# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup as BS

import sumario.blueprints.submission as submission

from ..helpers import (
    check_is_equal,
    url_for,
    with_tst_request_context,
    with_tst_client,
    with_tst_relay,
    with_tst_user,
)


@with_tst_request_context
def test_render_html_sorts_context(*args, **kwargs):
    extra_context = {"form": {"delta": 42, "bravo": 42, "charlie": 42, "alpha": 42, "8675309": 42}}
    bs = BS(submission.render_html(**extra_context), "html5lib")
    sorted_keys = [row.text.strip() for row in bs.findAll("td", attrs={"class": "form-key"})]
    check_is_equal(sorted_keys, ["8675309", "alpha", "bravo", "charlie", "delta"])


@with_tst_request_context
@with_tst_client
def test_submission_invalid_uuid(*args, **kwargs):
    test_client = kwargs["test_client"]

    response = test_client.post(url_for("submission.submission", uuid="foobar"))
    check_is_equal(response.status_code, 404)


@with_tst_request_context
@with_tst_client
@with_tst_user
@with_tst_relay
def test_submission_valid_uuid_without_referrer(*args, **kwargs):
    test_client = kwargs["test_client"]
    test_relay = kwargs["test_relay"]

    check_is_equal(test_relay.submissions.count(), 0)

    response = test_client.post(url_for("submission.submission", uuid=test_relay.uuid), data={"foobar": 42})
    check_is_equal(response.status_code, 302)

    location = response.headers["Location"]
    check_is_equal(location, "http://localhost:8443/success?referrer=")

    submission = test_relay.submissions.one()
    check_is_equal(submission.client_addr, "127.0.0.1")


@with_tst_request_context
@with_tst_client
@with_tst_user
@with_tst_relay
def test_submission_valid_uuid_with_referrer(*args, **kwargs):
    test_client = kwargs["test_client"]
    test_relay = kwargs["test_relay"]

    check_is_equal(test_relay.submissions.count(), 0)

    response = test_client.post(
        url_for("submission.submission", uuid=test_relay.uuid),
        data={"foobar": 42},
        headers={"Referer": "Hello, world!"},
    )
    check_is_equal(response.status_code, 302)

    location = response.headers["Location"]
    check_is_equal(location, "http://localhost:8443/success?referrer=Hello%2C%20world%21")

    submission = test_relay.submissions.one()
    check_is_equal(submission.client_addr, "127.0.0.1")


@with_tst_request_context
@with_tst_client
def test_submission_success_without_referrer(*args, **kwargs):
    test_client = kwargs["test_client"]

    response = test_client.get(url_for("submission.success"))
    check_is_equal(response.status_code, 200)

    bs = BS(response.data, "html5lib")
    referrer = bs.find("a", id="referrer")
    check_is_equal(referrer["href"], "#")


@with_tst_request_context
@with_tst_client
def test_submission_success_with_referrer(*args, **kwargs):
    test_client = kwargs["test_client"]

    response = test_client.get("{}?referrer=Hello%2C%20world%21".format(url_for("submission.success")))
    check_is_equal(response.status_code, 200)

    bs = BS(response.data, "html5lib")
    referrer = bs.find("a", id="referrer")
    check_is_equal(referrer["href"], "Hello, world!")


@with_tst_request_context
@with_tst_client
@with_tst_user
@with_tst_relay
def test_submission_user_not_in_good_standing(*args, **kwargs):
    test_client = kwargs["test_client"]
    test_relay = kwargs["test_relay"]

    _user_in_good_standing_orig = submission._user_in_good_standing
    submission._user_in_good_standing = lambda user: False

    response = test_client.post(
        url_for("submission.submission", uuid=test_relay.uuid),
        data={"foobar": 42},
        headers={"Referer": "Hello, world!"},
    )
    check_is_equal(response.status_code, 302)

    location = response.headers["Location"]
    check_is_equal(location, "http://localhost:8443/submission/nocredits?referrer=Hello%2C%20world%21")

    submission._user_in_good_standing = _user_in_good_standing_orig


@with_tst_request_context
@with_tst_client
def test_submission_nocredits_without_referrer(*args, **kwargs):
    test_client = kwargs["test_client"]

    response = test_client.get(url_for("submission.nocredits"))
    check_is_equal(response.status_code, 200)

    bs = BS(response.data, "html5lib")
    referrer = bs.find("a", id="referrer")
    check_is_equal(referrer["href"], "#")


@with_tst_request_context
@with_tst_client
def test_submission_nocredits_with_referrer(*args, **kwargs):
    test_client = kwargs["test_client"]

    response = test_client.get("{}?referrer=Hello%2C%20world%21".format(url_for("submission.nocredits")))
    check_is_equal(response.status_code, 200)

    bs = BS(response.data, "html5lib")
    referrer = bs.find("a", id="referrer")
    check_is_equal(referrer["href"], "Hello, world!")


@with_tst_request_context
@with_tst_client
@with_tst_user
@with_tst_relay
def test_submission_possible_bot(*args, **kwargs):
    test_client = kwargs["test_client"]
    test_relay = kwargs["test_relay"]

    response = test_client.post(url_for("submission.submission", uuid=test_relay.uuid))
    check_is_equal(response.status_code, 302)

    location = response.headers["Location"]
    check_is_equal(location, "http://localhost:8443/submission/possiblebot?referrer=")

    response = test_client.get(location)
    check_is_equal(response.status_code, 200)
