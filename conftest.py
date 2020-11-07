import pytest


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """Enable DB access for all tests

    http://pytest-django.readthedocs.io/en/latest/faq.html#how-can-i-give-database-access-to-all-my-tests-without-the-django-db-marker"""
    pass
