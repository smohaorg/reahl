
from __future__ import print_function, unicode_literals, absolute_import, division
from reahl.tofu import Fixture

from reahl.sqlalchemysupport import Session
from reahl.webdev.tools import Browser, XPath

from reahl.doc.examples.tutorial.sessionscopebootstrap.sessionscopebootstrap import SessionScopeUI, User

from reahl.web_dev.fixtures import web_fixture
from reahl.sqlalchemysupport_dev.fixtures import sql_alchemy_fixture
from reahl.domain_dev.fixtures import party_account_fixture


class SessionScopeFixture(Fixture):
    password = 'topsecret'

    def new_user(self):
        user = User(name='John Doe', email_address='johndoe@some.org')
        user.set_password(self.password)
        Session.add(user)
        return user

session_scope_fixture = SessionScopeFixture.as_pytest_fixture()


def demo_setup(sql_alchemy_fixture, session_scope_fixture):
    sql_alchemy_fixture.commit = True
    with sql_alchemy_fixture.context:
        session_scope_fixture.new_user()




def test_logging_in(web_fixture, session_scope_fixture):
    """A user can log in by going to the Log in page.
       The name of the currently logged in user is displayed on the home page."""

    with web_fixture.context:
        browser = Browser(web_fixture.new_wsgi_app(site_root=SessionScopeUI))
        user = session_scope_fixture.user

        browser.open('/')
        browser.click(XPath.link_with_text('Log in'))

        browser.type(XPath.input_labelled('Email'), 'johndoe@some.org')
        browser.type(XPath.input_labelled('Password'), 'topsecret')
        browser.click(XPath.button_labelled('Log in'))

        browser.click(XPath.link_with_text('Home'))
        assert browser.is_element_present(XPath.paragraph_containing('Welcome John Doe'))
    

def test_email_retained(web_fixture, session_scope_fixture):
    """The email address used when last logged in is always pre-populated on the Log in page."""

    with web_fixture.context:
        browser = Browser(web_fixture.new_wsgi_app(site_root=SessionScopeUI))
        user = session_scope_fixture.user

        browser.open('/')
        browser.click(XPath.link_with_text('Log in'))

        browser.type(XPath.input_labelled('Email'), 'johndoe@some.org')
        browser.type(XPath.input_labelled('Password'), 'topsecret')
        browser.click(XPath.button_labelled('Log in'))

        # Go away from the page, then back
        browser.click(XPath.link_with_text('Home'))
        browser.click(XPath.link_with_text('Log in'))

        # .. then the email is still pre-populated
        typed_value = browser.get_value(XPath.input_labelled('Email'))
        assert typed_value == 'johndoe@some.org'
    

def test_domain_exception(web_fixture, session_scope_fixture):
    """Typing the wrong password results in an error message being shown to the user."""

    with web_fixture.context:
        browser = Browser(web_fixture.new_wsgi_app(site_root=SessionScopeUI))
        user = session_scope_fixture.user

        browser.open('/')
        browser.click(XPath.link_with_text('Log in'))

        browser.type(XPath.input_labelled('Email'), 'johndoe@some.org')
        browser.type(XPath.input_labelled('Password'), 'wrong password')
        browser.click(XPath.button_labelled('Log in'))

        assert browser.is_element_present(XPath.div_containing('The email/password given do not match'))
