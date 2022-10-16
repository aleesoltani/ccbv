from pathlib import Path

import pytest
from django.core.management import call_command
from django.test.client import Client
from django.urls import reverse
from pytest_django.asserts import assertHTMLEqual, assertNumQueries
from pytest_django.fixtures import SettingsWrapper
from pytest_subtests import SubTests


RENDERED_VIEWS = [
    (
        "homepage.html",
        184,
        reverse("home"),
    ),
    (
        "version-detail.html",
        183,
        reverse("version-detail", kwargs={"package": "django", "version": "4.0"}),
    ),
    (
        "module-detail.html",
        12,
        reverse(
            "module-detail",
            kwargs={
                "package": "django",
                "version": "4.0",
                "module": "django.views.generic.edit",
            },
        ),
    ),
    (
        "klass-detail.html",
        36,
        reverse(
            "klass-detail",
            kwargs={
                "package": "django",
                "version": "4.0",
                "module": "django.views.generic.edit",
                "klass": "FormView",
            },
        ),
    ),
    (
        "klass-detail.html",
        39,
        reverse("klass-detail-shortcut", kwargs={"klass": "FormView"}),
    ),
    # Detail pages with wRonGLY CasEd arGuMEnTs
    (
        "fuzzy-version-detail.html",
        183,
        reverse("version-detail", kwargs={"package": "DJANGO", "version": "4.0"}),
    ),
    (
        "fuzzy-module-detail.html",
        13,
        reverse(
            "module-detail",
            kwargs={
                "package": "DJANGO",
                "version": "4.0",
                "module": "DJANGO.VIEWS.GENERIC.EDIT",
            },
        ),
    ),
    (
        "fuzzy-klass-detail.html",
        36,
        reverse(
            "klass-detail",
            kwargs={
                "package": "DJANGO",
                "version": "4.0",
                "module": "DJANGO.VIEWS.GENERIC.EDIT",
                "klass": "fORMvIEW",
            },
        ),
    ),
    (
        "fuzzy-klass-detail.html",
        39,
        reverse("klass-detail-shortcut", kwargs={"klass": "fORMvIEW"}),
    ),
]


@pytest.mark.django_db
def test_page_html(
    client: Client, settings: SettingsWrapper, subtests: SubTests
) -> None:
    """
    Checks that the pages in the array above match the reference files in cbv/tests/_page_snapshots/.

    This test is intended to prevent regressions when refactoring views/templates.
    As well as ensuring the HTML hasn't materially changed,
    we also check the number of queries made when rendering the page.

    If the reference files legitimately need to change, they can be
    re-generated by temporarily uncommenting the appropriate lines at the
    bottom of the test.
    """
    # Load a couple of versions of Django.
    # It doesn't matter what they are, just that they stay consistent.
    call_command("loaddata", "project.json")
    call_command("loaddata", "3.2.json")
    call_command("loaddata", "4.0.json")

    # We set this to avoid an error from whitenoise when rendering templates:
    # ValueError: Missing staticfiles manifest entry for 'bootstrap.css'
    settings.STATICFILES_STORAGE = None

    for filename, num_queries, url in RENDERED_VIEWS:
        with subtests.test(url=url):
            with assertNumQueries(num_queries):
                response = client.get(url)

            html = response.rendered_content
            path = Path("cbv/tests/_page_snapshots", filename)

            # Uncomment the below to re-generate the reference files
            # when they need to change for a legitimate reason.
            # DO NOT commit this uncommented!
            # path.write_text(html)

            expected = path.read_text()

            # This forces a useful error in the case of a mismatch.
            # We have to ignore the type because accessing __wrapped__ is pretty odd.
            assertHTMLEqual.__wrapped__.__self__.maxDiff = None  # type: ignore
            assertHTMLEqual(html, expected)
