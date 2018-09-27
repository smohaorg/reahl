# Copyright 2018 Reahl Software Services (Pty) Ltd. All rights reserved.
#
#    This file is part of Reahl.
#
#    Reahl is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation; version 3 of the License.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.


from __future__ import print_function, unicode_literals, absolute_import, division

from sqlalchemy import Column, Integer

from reahl.tofu import Fixture, expected, scenario, uses
from reahl.tofu.pytestsupport import with_fixtures

from reahl.web_dev.fixtures import WebFixture
from reahl.webdev.tools import XPath, Browser
from reahl.web.fw import Widget
from reahl.web.ui import Form, Div, SelectInput, Label, P, RadioButtonSelectInput, CheckboxSelectInput, \
    CheckboxInput, ButtonInput, TextInput
from reahl.component.modelinterface import Field, BooleanField, MultiChoiceField, ChoiceField, Choice, exposed, IntegerField, \
    EmailField, Event
from reahl.component.exceptions import ProgrammerError
from reahl.web_dev.inputandvalidation.test_widgetqueryargs import QueryStringFixture
from reahl.sqlalchemysupport import Base, Session
from reahl.sqlalchemysupport_dev.fixtures import SqlAlchemyFixture


@uses(web_fixture=WebFixture)
class ResponsiveDisclosureFixture(Fixture):

    def new_ModelObject(self):
        class ModelObject(object):
            @exposed
            def fields(self, fields):
                fields.choice = ChoiceField([Choice(1, IntegerField(label='One')),
                                             Choice(2, IntegerField(label='Two')),
                                             Choice(3, IntegerField(label='Three'))],
                                            default=1,
                                            label='Choice')
        return ModelObject

    def new_MyChangingWidget(self):
        class MyChangingWidget(Div):
            def __init__(self, view, trigger_input, model_object):
                self.trigger_input = trigger_input
                self.model_object = model_object
                super(MyChangingWidget, self).__init__(view, css_id='dave')
                self.enable_refresh()
                trigger_input.enable_notify_change(self, self.query_fields.fancy_state)
                self.add_child(P(self.view, text='My state is now %s' % self.fancy_state))

            @property
            def fancy_state(self):
                return self.model_object.choice

            @exposed
            def query_fields(self, fields):
                fields.fancy_state = self.model_object.fields.choice

        return MyChangingWidget

    def new_MainWidget(self):
        fixture = self
        class MainWidget(Widget):
            def __init__(self, view):
                super(MainWidget, self).__init__(view)
                an_object = fixture.ModelObject()
                form = self.add_child(fixture.MyForm(view, an_object))
                self.add_child(fixture.MyChangingWidget(view, form.change_trigger_input, an_object))

        return MainWidget

    def new_MyForm(self):
        class MyForm(Form):
            def __init__(self, view, an_object):
                super(MyForm, self).__init__(view, 'myform')
                self.change_trigger_input = SelectInput(self, an_object.fields.choice)
                self.add_child(Label(view, for_input=self.change_trigger_input))
                self.add_child(self.change_trigger_input)
        return MyForm


class ResponsiveWidgetScenarios(ResponsiveDisclosureFixture):
    @scenario
    def select_input(self):
        fixture = self

        def change_value(browser):
            browser.select(XPath.select_labelled('Choice'), 'Three')
        self.change_value = change_value
        self.initial_state = 1
        self.changed_state = 3

    @scenario
    def radio_buttons(self):
        fixture = self

        class MyForm(Form):
            def __init__(self, view, an_object):
                super(MyForm, self).__init__(view, 'myform')
                self.change_trigger_input = RadioButtonSelectInput(self, an_object.fields.choice)
                self.change_trigger_input.set_id('marvin')
                self.add_child(Label(view, for_input=self.change_trigger_input))
                self.add_child(self.change_trigger_input)
        self.MyForm = MyForm

        def change_value(browser):
            browser.click(XPath.input_labelled('Three'))
        self.change_value = change_value
        self.initial_state = 1
        self.changed_state = 3

    @scenario
    def single_valued_checkbox(self):
        fixture = self

        class ModelObject(object):
            @exposed
            def fields(self, fields):
                fields.choice = BooleanField(default=False, label='Choice',
                                             true_value='✓', false_value='⍻')
        self.ModelObject = ModelObject

        class MyForm(Form):
            def __init__(self, view, an_object):
                super(MyForm, self).__init__(view, 'myform')
                self.change_trigger_input = CheckboxInput(self, an_object.fields.choice)
                self.change_trigger_input.set_id('marvin')
                self.add_child(Label(view, for_input=self.change_trigger_input))
                self.add_child(self.change_trigger_input)
        self.MyForm = MyForm

        def change_value(browser):
            browser.click(XPath.input_labelled('Choice'))
        self.change_value = change_value
        self.initial_state = False
        self.changed_state = True

    @scenario
    def multi_valued_checkbox_select(self):
        fixture = self

        class ModelObject(object):
            @exposed
            def fields(self, fields):
                fields.choice = MultiChoiceField([Choice(1, IntegerField(label='One')),
                                                  Choice(2, IntegerField(label='Two')),
                                                  Choice(3, IntegerField(label='Three'))],
                                                 default=[1],
                                                 label='Choice')
        self.ModelObject = ModelObject

        class MyForm(Form):
            def __init__(self, view, an_object):
                super(MyForm, self).__init__(view, 'myform')
                self.change_trigger_input = CheckboxSelectInput(self, an_object.fields.choice)
                self.change_trigger_input.set_id('marvin')
                self.add_child(Label(view, for_input=self.change_trigger_input))
                self.add_child(self.change_trigger_input)
        self.MyForm = MyForm

        def change_value(browser):
            browser.click(XPath.input_labelled('Three'))
        self.change_value = change_value
        self.initial_state = [1]
        self.changed_state = [1, 3]

    @scenario
    def multi_valued_checkbox_select_with_single_choice_corner_case_empty_a_list(self):
        self.multi_valued_checkbox_select()
        fixture = self

        class ModelObject(object):
            @exposed
            def fields(self, fields):
                fields.choice = MultiChoiceField([Choice(1, IntegerField(label='One'))],
                                                 default=[1],
                                                 label='Choice')
        self.ModelObject = ModelObject
        #self.MyForm from multi_valued_checkbox_select

        def change_value(browser):
            browser.click(XPath.input_labelled('One'))
        self.change_value = change_value
        self.initial_state = [1]
        self.changed_state = []

    @scenario
    def multi_valued_checkbox_select_with_single_choice_corner_case_add_to_empty_list(self):
        self.multi_valued_checkbox_select()
        fixture = self

        class ModelObject(object):
            @exposed
            def fields(self, fields):
                fields.choice = MultiChoiceField([Choice(1, IntegerField(label='One'))],
                                                 default=[],
                                                 label='Choice')
        self.ModelObject = ModelObject
        #self.MyForm from multi_valued_checkbox_select

        def change_value(browser):
            browser.click(XPath.input_labelled('One'))
        self.change_value = change_value
        self.initial_state = []
        self.changed_state = [1]

    @scenario
    def multi_valued_select(self):
        fixture = self

        class ModelObject(object):
            @exposed
            def fields(self, fields):
                fields.choice = MultiChoiceField([Choice(1, IntegerField(label='One')),
                                                  Choice(2, IntegerField(label='Two')),
                                                  Choice(3, IntegerField(label='Three'))],
                                                 default=[1],
                                                 label='Choice')
        self.ModelObject = ModelObject

        class MyForm(Form):
            def __init__(self, view, an_object):
                super(MyForm, self).__init__(view, 'myform')
                self.change_trigger_input = SelectInput(self, an_object.fields.choice)
                self.change_trigger_input.set_id('marvin')
                self.add_child(Label(view, for_input=self.change_trigger_input))
                self.add_child(self.change_trigger_input)
        self.MyForm = MyForm

        def change_value(browser):
            browser.select(XPath.select_labelled('Choice'), 'Three')
        self.change_value = change_value
        self.initial_state = [1]
        self.changed_state = [1, 3]


@with_fixtures(WebFixture, QueryStringFixture, ResponsiveWidgetScenarios)
def test_input_values_can_be_widget_arguments(web_fixture, query_string_fixture, responsive_widget_scenarios):
    """Widget query arguments can be linked to the value of an input, which means the Widget will be re-rendered if the input value changes."""

    fixture = responsive_widget_scenarios

    wsgi_app = web_fixture.new_wsgi_app(enable_js=True, child_factory=fixture.MainWidget.factory())
    web_fixture.reahl_server.set_app(wsgi_app)
    browser = web_fixture.driver_browser
    browser.open('/')
    
    assert browser.wait_for(query_string_fixture.is_state_now, fixture.initial_state)
    fixture.change_value(browser)
    assert browser.wait_for(query_string_fixture.is_state_now, fixture.changed_state)


@with_fixtures(WebFixture, QueryStringFixture, ResponsiveDisclosureFixture)
def test_changing_values_do_not_disturb_other_hash_state(web_fixture, query_string_fixture, responsive_disclosure_fixture):
    """When an Input updates a linked Widget, other values in the hash are preserved."""

    fixture = responsive_disclosure_fixture

    wsgi_app = web_fixture.new_wsgi_app(enable_js=True, child_factory=fixture.MainWidget.factory())
    web_fixture.reahl_server.set_app(wsgi_app)
    browser = web_fixture.driver_browser
    browser.open('/')

    assert browser.wait_for(query_string_fixture.is_state_now, 1)
    browser.set_fragment('#choice=2&other_var=other_value')
    browser.select(XPath.select_labelled('Choice'), 'Three')
    assert browser.get_fragment() == '#other_var=other_value&choice=3'



class MultipleTriggerFixture(Fixture):
    def is_widget_blocked(self, browser):
        changing_widget_xpath = XPath('//div[@id="changing_widget_id"]')
        changing_widget_blocked_xpath = XPath('%s/div[@class="blockUI"]' % changing_widget_xpath)
        return browser.is_element_present(changing_widget_blocked_xpath)


@with_fixtures(WebFixture, QueryStringFixture, MultipleTriggerFixture)
def test_invalid_values_block_out_dependent_widgets(web_fixture, query_string_fixture, multiple_trigger_fixture):
    """If the user types an invalid value into an input serving as argument for one or more Widgets, the widgets are blocked out"""

    class ModelObject(object):
        @exposed
        def fields(self, fields):
            fields.choice = ChoiceField([Choice(1, IntegerField(label='One')),
                                         Choice(2, IntegerField(label='Two')),
                                         Choice(3, IntegerField(label='Three'))],
                                        default=1,
                                        label='Choice')
            fields.another_choice = ChoiceField([Choice(4, IntegerField(label='Four')),
                                         Choice(5, IntegerField(label='Five')),
                                         Choice(6, IntegerField(label='Six'))],
                                        default=4,
                                        label='Another Choice')

    class MyForm(Form):
        def __init__(self, view, an_object):
            super(MyForm, self).__init__(view, 'myform')
            self.change_trigger_input = TextInput(self, an_object.fields.choice)
            self.add_child(Label(view, for_input=self.change_trigger_input))
            self.add_child(self.change_trigger_input)

            self.sibling_change_trigger_input = TextInput(self, an_object.fields.another_choice)
            self.add_child(Label(view, for_input=self.sibling_change_trigger_input))
            self.add_child(self.sibling_change_trigger_input)

    class MyChangingWidget(Div):
        def __init__(self, view, trigger_input, sibling_trigger_input, model_object):
            self.trigger_input = trigger_input
            self.sibling_trigger_input = sibling_trigger_input
            self.model_object = model_object
            super(MyChangingWidget, self).__init__(view, css_id='changing_widget_id')
            self.enable_refresh()
            trigger_input.enable_notify_change(self, self.query_fields.fancy_state)
            sibling_trigger_input.enable_notify_change(self, self.query_fields.another_fancy_state)
            self.add_child(P(self.view, text='My state is now %s and %s' % (self.fancy_state, self.another_fancy_state)))

        @property
        def fancy_state(self):
            return self.model_object.choice

        @property
        def another_fancy_state(self):
            return self.model_object.another_choice

        @exposed
        def query_fields(self, fields):
            fields.fancy_state = self.model_object.fields.choice
            fields.another_fancy_state = self.model_object.fields.another_choice


    class MainWidget(Widget):
        def __init__(self, view):
            super(MainWidget, self).__init__(view)
            an_object = ModelObject()
            form = self.add_child(MyForm(view, an_object))
            self.add_child(MyChangingWidget(view, form.change_trigger_input, form.sibling_change_trigger_input, an_object))


    wsgi_app = web_fixture.new_wsgi_app(enable_js=True, child_factory=MainWidget.factory())
    web_fixture.reahl_server.set_app(wsgi_app)
    browser = web_fixture.driver_browser
    browser.open('/')

    # Case: an invalid option blocks the Widget out, does not refresh
    assert not multiple_trigger_fixture.is_widget_blocked(browser)    
    assert query_string_fixture.is_state_now('1 and 4')

    browser.type(XPath.input_labelled('Choice'), 'not a valid option')
    browser.press_tab()
    assert browser.wait_for(multiple_trigger_fixture.is_widget_blocked, browser)    
    assert browser.wait_for(query_string_fixture.is_state_now, '1 and 4')

    # Case: a valid option changes does nothing if its sibling is still invalid
    browser.type(XPath.input_labelled('Another Choice'), '5')
    assert browser.wait_for(multiple_trigger_fixture.is_widget_blocked, browser)    
    assert browser.wait_for(query_string_fixture.is_state_now, '1 and 4')

    # Case: when all siblings are valid, the widget is refreshed, and it includes all relevant changed values
    browser.type(XPath.input_labelled('Choice'), '2')
    browser.press_tab()
    assert browser.wait_for_not(multiple_trigger_fixture.is_widget_blocked, browser)    
    assert browser.wait_for(query_string_fixture.is_state_now, '2 and 5')


def while_the_widget_is_being_refreshed_te_form_is_blocked():
    assert None

@with_fixtures(WebFixture, ResponsiveDisclosureFixture, SqlAlchemyFixture, QueryStringFixture)
def test_form_values_are_not_persisted_until_form_is_submitted(web_fixture, responsive_disclosure_fixture, sql_alchemy_fixture, query_string_fixture):
    """Values submitted via ajax are used only to redraw the screen; they are only changed on the underlying domain once the form is submitted."""

    fixture = responsive_disclosure_fixture

    class ModelObject(Base):
        __tablename__ = 'test_responsive_disclosure_rollback'
        id = Column(Integer, primary_key=True)
        number = Column(Integer)
        choice = Column(Integer, default=1)

        @exposed
        def fields(self, fields):
            fields.choice = ChoiceField([Choice(1, IntegerField(label='One')),
                                         Choice(2, IntegerField(label='Two')),
                                         Choice(3, IntegerField(label='Three'))],
                                         label='Choice')
    fixture.ModelObject = ModelObject

    class FormWithButton(fixture.MyForm):
        def __init__(self, view, an_object):
            super(FormWithButton, self).__init__(view, an_object)

            self.define_event_handler(self.events.submit)
            self.add_child(ButtonInput(self, self.events.submit))

        @exposed
        def events(self, events):
            events.submit = Event(label='Submit')

    fixture.MyForm = FormWithButton

    with sql_alchemy_fixture.persistent_test_classes(ModelObject):

        model_object = ModelObject(number=123)
        Session.add(model_object)

        class MainWidget(Widget):
            def __init__(self, view):
                super(MainWidget, self).__init__(view)
                an_object = model_object
                form = self.add_child(fixture.MyForm(view, an_object))
                self.add_child(fixture.MyChangingWidget(view, form.change_trigger_input, an_object))
        fixture.MainWidget = MainWidget

        wsgi_app = web_fixture.new_wsgi_app(enable_js=True, child_factory=MainWidget.factory())
        web_fixture.reahl_server.set_app(wsgi_app)
        browser = web_fixture.driver_browser
        browser.open('/')

        assert model_object.choice == 1
        browser.click(XPath.option_with_text('Three'))
    
        assert browser.wait_for(query_string_fixture.is_state_now, 3)  # The screen was updated,
        assert model_object.choice == 1                                # but the database not.

        browser.click(XPath.button_labelled('Submit'))
        assert browser.wait_for(query_string_fixture.is_state_now, 3) 
        assert model_object.choice == 3                                # Now the database is updated too.



@with_fixtures(WebFixture)
def test_inputs_effect_other_parts_of_form(web_fixture):
    """Inputs can trigger refresh of Widgets that contain other inputs in the same form"""
    assert None, 'TODO: relax check_input_placement so that it only breaks if the form does NOT have a specific ID set (it should still break if the form ID is auto-generated'
    # We need to think carefully about this one.
    # It makes sense to let an input be refreshed anywhere on the page, as long as its form's ID is always going to be unchanged.
    # Perhaps the test to change first is test_check_input_placement (inputandvalidation/test_eventhandling.py)
    # ...but I still think we need to have a test here? because this is a requirement relating to responsive disclosure?


class DisclosedInputFixture(Fixture):

    def new_trigger_input_type(self):
        return CheckboxInput

    def new_model_object(self):
        class ModelObject(object):
            def __init__(self):
                self.trigger_field = True
                self.email = None

            @exposed
            def events(self, events):
                events.an_event = Event(label='click me')

            @exposed
            def fields(self, fields):
                fields.trigger_field = BooleanField(label='Trigger field')
                fields.email = EmailField(required=True, label='Email') #has required Validation Constraint
        return ModelObject()

    def new_MyForm(self):
        fixture = self
        class MyForm(Form):
            def __init__(self, view):
                super(MyForm, self).__init__(view, 'myform')

                checkbox_input = fixture.trigger_input_type(self,fixture.model_object.fields.trigger_field)
                self.add_child(Label(view, for_input=checkbox_input))
                self.add_child(checkbox_input)

                self.add_child(fixture.MyChangingWidget(self, checkbox_input, fixture.model_object))

                self.define_event_handler(fixture.model_object.events.an_event)
                self.add_child(ButtonInput(self, fixture.model_object.events.an_event))
        return MyForm

    def new_MyChangingWidget(self):
        fixture = self
        class MyChangingWidget(Div):
            def __init__(self, form, trigger_input, model_object):
                self.model_object = model_object
                super(MyChangingWidget, self).__init__(form.view, css_id='requiredinfoid')
                self.enable_refresh()
                trigger_input.enable_notify_change(self, self.query_fields.trigger_field)

                if self.model_object.trigger_field:
                    text_input = TextInput(form, self.model_object.fields.email)
                    self.add_child(Label(form.view, for_input=text_input))
                    self.add_child(text_input)

            @exposed
            def query_fields(self, fields):
                fields.trigger_field = self.model_object.fields.trigger_field
        return MyChangingWidget


@with_fixtures(WebFixture, DisclosedInputFixture)
def test_validation_of_undisclosed_yet_required_input(web_fixture, boolean_input_fixture):
    """If a Field has a required constraint, but its Input is not currently displayed as part of the form (because of the
       state of another Input), and the form is submitted, the constraint should not cause an exception(input was omitted)."""

    fixture = boolean_input_fixture

    model_object = fixture.model_object
    wsgi_app = web_fixture.new_wsgi_app(enable_js=True, child_factory=fixture.MyForm.factory())
    web_fixture.reahl_server.set_app(wsgi_app)
    browser = web_fixture.driver_browser
    browser.open('/')

    assert browser.is_element_present(XPath.input_labelled('Email'))
    browser.click(XPath.input_labelled('Trigger field'))
    assert not browser.is_element_present(XPath.input_labelled('Email'))
    browser.click(XPath.button_labelled('click me'))

    assert model_object.trigger_field == False
    assert not model_object.email


@with_fixtures(WebFixture, ResponsiveDisclosureFixture)
def test_trigger_input_may_not_be_on_refreshing_widget(web_fixture, responsive_disclosure_fixture):
    """You may not trigger one of your parents to refresh"""

    fixture = responsive_disclosure_fixture

    class ChangingWidget(fixture.MyChangingWidget):
        def __init__(self, view, form, model_object):
            super(ChangingWidget, self).__init__(view, form.change_trigger_input, model_object)
            self.add_child(form)

    class MainWidget(Widget):
        def __init__(self, view):
            super(MainWidget, self).__init__(view)
            model_object = fixture.ModelObject()
            form = fixture.MyForm(view, model_object)
            self.add_child(ChangingWidget(view, form, model_object))


    wsgi_app = web_fixture.new_wsgi_app(enable_js=True, child_factory=MainWidget.factory())
    web_fixture.reahl_server.set_app(wsgi_app)
    browser = web_fixture.driver_browser
    
    with expected(ProgrammerError, test='Inputs are not allowed where they can trigger themselves to be refreshed. Some inputs were incorrectly placed:\n\t<SelectInput name=choice> is refreshed by <ChangingWidget div id=dave> via field <ChoiceField name=choice>\n'):
        browser.open('/')


@with_fixtures(WebFixture, DisclosedInputFixture)
def test_correct_tab_order_for_responsive_widgets(web_fixture, boolean_input_trigger_fixture):
    """When a user TAB's out of an input that then triggers a change, the tab is ignored and focus stays on the original input so that the tab order can be recalculated."""

    fixture = boolean_input_trigger_fixture
    fixture.trigger_input_type = TextInput

    model_object = fixture.model_object
    model_object.trigger_field = False
    wsgi_app = web_fixture.new_wsgi_app(enable_js=True, child_factory=fixture.MyForm.factory())

    web_fixture.reahl_server.set_app(wsgi_app)
    browser = web_fixture.driver_browser
    browser.open('/')

    # Case: a new input appears in next tab order position
    assert browser.get_value(XPath.input_labelled('Trigger field')) == 'off'
    browser.press_tab()
    assert browser.is_focus_on(XPath.input_labelled('Trigger field'))
    browser.type(XPath.input_labelled('Trigger field'), 'on')
    browser.press_tab()
    browser.press_tab()
    assert browser.is_focus_on(XPath.input_labelled('Email'))
    
    # Case: an input disappears from the next tab order position
    browser.type(XPath.input_labelled('Trigger field'), 'off')
    browser.press_tab()
    browser.press_tab()
    assert browser.is_focus_on(XPath.button_labelled('click me'))


@with_fixtures(WebFixture, DisclosedInputFixture)
def test_ignore_button_click_on_change(web_fixture, boolean_input_trigger_fixture):
    """If a button click triggers a change to the page (due to a modified TextInput losing focus), the click is ignored."""

    assert None
    fixture = boolean_input_trigger_fixture
    fixture.trigger_input_type = TextInput

    model_object = fixture.model_object
    model_object.trigger_field = False
    wsgi_app = web_fixture.new_wsgi_app(enable_js=True, child_factory=fixture.MyForm.factory())

    web_fixture.reahl_server.set_app(wsgi_app)
    browser = web_fixture.driver_browser
    browser.open('/')

    assert browser.get_value(XPath.input_labelled('Trigger field')) == 'off'
    assert not browser.is_element_present(XPath.input_labelled('Email'))
    browser.type(XPath.input_labelled('Trigger field'), 'on')
    with browser.no_page_load_expected():
        browser.click(XPath.button_labelled('click me'))
    assert browser.is_element_present(XPath.input_labelled('Email'))



# Naming of notifier.
# Clashing names of things on the hash (larger issue)

# DONE: break if a user sends a ChoiceField to a CheckboxSelectInput
# TODO: test that things like TextInput can give input to a MultiChoiceField by doing, eg input.split(',') in the naive case
# DONE: test that you cannot trigger one of your parents to refresh.
# DONE: if you tab out of something, you should tab to the next thing as per the regenerated screen
# DONE: test_refresh_widget_without_query_fields_raises_error that if you call enable_refresh without args, that the widget at least has some query_fields?? (Programming error)
# TODO: (related to xsrf token implementation maybe?) form id should really be unique amongst all pages in a UserInterface, because invalid input is stored in the DB using the keys: UI.name, form.eventChannel.name
# DONE: deal better with discriminators on input names. has to be passed through to the field for extract_from OR better do away with it somehow? I think we should remove the discriminator story. Rather change register_with_form to break if names clash. And provide a way to then override the "qualified_name" of a Field, like in: field.as_with_qualified_name("x") or something.
# DONE: when an input is tied to a multichoicefield with only one choice, should the input be disabled as the only choice is the default, and cannot change. Inconsistent state observed when uncheck'ing such item: unchecked, but responsive dependend is displayed.
# TODO: deal with onchange that happens in response to a text field that loses focus because you typed in it, and then clicked on a button
# DONE: do not do the ajax refresh if there are validation errors on the ajax input trigger 
# TODO: maybe move attribs on js objects from options to this???
# TODO: prevent double-click on a button (once clisked, it disables itself from further clicks forever)

# DONE: see: multi_value_empty_the_list when an input is tied to a multichoicefield with only one choice, should the input be disabled as the only choice is the default, and cannot change. Inconsistent state observed when uncheck'ing such item: unchecked, but responsive dependend is displayed.
# TODO: found that this test seems to hang regularly(not when run individually, and the xpra chrome window stays open): pytest  reahl/web_dev/bootstrap/test_tabbedpanel.py::test_clicking_on_multi_tab, more spcifically: pytest  reahl/web_dev/bootstrap/test_tabbedpanel.py::"test_clicking_on_multi_tab[web_fixture1-panel_switch_fixture1-tabbed_panel_ajax_fixture1]"


## This is where the test_tabbedpanel tests get stuck
#   File "/usr/lib/python3.6/socket.py", line 586 in readinto
#   File "/vagrant/reahl-webdev/reahl/webdev/webserver.py", line 210 in connection_is_pending
#
#
# Thread 0x00007ff477b89700 (most recent call first):
#   File "/usr/lib/python3.6/socket.py", line 586 in readinto
#   File "/usr/lib/python3.6/http/client.py", line 258 in _read_status
#   File "/usr/lib/python3.6/http/client.py", line 297 in begin
#   File "/usr/lib/python3.6/http/client.py", line 1331 in getresponse
#   File "/home/vagrant/.virtualenvs/python3.6/lib/python3.6/site-packages/selenium/webdriver/remote/remote_connection.py", line 433 in _request
#   File "/home/vagrant/.virtualenvs/python3.6/lib/python3.6/site-packages/selenium/webdriver/remote/remote_connection.py", line 401 in execute
#   File "/vagrant/reahl-webdev/reahl/webdev/webserver.py", line 284 in doit
#   File "/usr/lib/python3.6/threading.py", line 864 in run
#   File "/usr/lib/python3.6/threading.py", line 916 in _bootstrap_inner
#   File "/usr/lib/python3.6/threading.py", line 884 in _bootstrap
#
# Thread 0x00007ff483310740 (most recent call first):
#   File "/vagrant/reahl-webdev/reahl/webdev/webserver.py", line 210 in connection_is_pending
#   File "/vagrant/reahl-webdev/reahl/webdev/webserver.py", line 198 in serve_async
#   File "/vagrant/reahl-webdev/reahl/webdev/webserver.py", line 538 in serve_until
#   File "/vagrant/reahl-webdev/reahl/webdev/webserver.py", line 300 in wrapped_execute
#   File "/home/vagrant/.virtualenvs/python3.6/lib/python3.6/site-packages/selenium/webdriver/remote/webdriver.py", line 234 in execute
#   File "/home/vagrant/.virtualenvs/python3.6/lib/python3.6/site-packages/selenium/webdriver/remote/webdriver.py", line 510 in close
#   File "/vagrant/reahl-webdev/reahl/webdev/fixtures.py", line 147 in restart_chrome_session
#   File "/vagrant/reahl-web/reahl/web_dev/bootstrap/test_tabbedpanel.py", line 220 in ensure_disabled_js_files_not_cached
#   File "/vagrant/reahl-web/reahl/web_dev/bootstrap/test_tabbedpanel.py", line 235 in test_clicking_on_different_tabs_switch
#   File "/vagrant/reahl-tofu/reahl/tofu/pytestsupport.py", line 153 in test_with_fixtures
#   File "/home/vagrant/.virtualenvs/python3.6/lib/python3.6/site-packages/_pytest/python.py", line 196 in pytest_pyfunc_call
#   File "/home/vagrant/.virtualenvs/python3.6/lib/python3.6/site-packages/pluggy/callers.py", line 180 in _multicall
