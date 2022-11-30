import libyang
import pytest
from mock import Mock, call, ANY

from yangvoodoo.SchemaData import Expander


class TestExpander(Expander):
    def __init__(self, yang_module, log):
        super().__init__(yang_module, log)
        self.callback_open_containing_node = Mock()
        self.callback_close_containing_node = Mock()
        self.callback_write_leaf = Mock()
        self.callback_open_leaflist = Mock()
        self.callback_close_leaflist = Mock()
        self.callback_open_choice = Mock()
        self.callback_close_choice = Mock()
        self.callback_open_case = Mock()
        self.callback_close_case = Mock()
        self.callback_open_list = Mock()
        self.callback_close_list = Mock()
        self.callback_open_list_element = Mock()
        self.callback_close_list_element = Mock()


@pytest.fixture
def subject(mocker):
    return TestExpander("testforms", Mock())


def test_lists(subject):
    subject.process(open("templates/forms/simplelist2.xml").read())

    # Assert Leafs
    assert subject.callback_write_leaf.mock_calls == [
        call(ANY, '""', default=None, key=False, node_id="/testforms:topleaf"),
        call(
            ANY,
            "'world'",
            default="put something here",
            node_id="/testforms:toplevel/hello",
            key=False,
        ),
        call(
            ANY,
            '""',
            default=None,
            key=False,
            node_id="/testforms:toplevel/mychoice/mycase1/box/clown",
        ),
        call(
            ANY,
            '""',
            default=None,
            key=False,
            node_id="/testforms:toplevel/mychoice/mycase3/empty",
        ),
        call(
            ANY,
            "'A'",
            default=None,
            key=True,
            node_id="/testforms:toplevel/simplelist[simplekey='A']/simplekey",
        ),
        call(
            ANY,
            "'non key value goes here'",
            default="non key value goes here",
            node_id="/testforms:toplevel/simplelist[simplekey='A']/simplenonkey",
            key=False,
        ),
        call(
            ANY,
            "'B'",
            default=None,
            node_id="/testforms:toplevel/simplelist[simplekey='B']/simplekey",
            key=True,
        ),
        call(
            ANY,
            "'non key value goes here'",
            default="non key value goes here",
            node_id="/testforms:toplevel/simplelist[simplekey='B']/simplenonkey",
            key=False,
        ),
        call(
            ANY,
            "'withdefault'",
            default="withdefault",
            node_id="/testforms:toplevel/still-in-top/of-the-world",
            key=False,
        ),
        call(
            ANY,
            '""',
            default=None,
            key=False,
            node_id="/testforms:toplevel/still-in-top/pointer",
        ),
        call(
            ANY,
            '""',
            default=None,
            key=False,
            node_id="/testforms:toplevel/still-in-top/a",
        ),
        call(
            ANY,
            "'true'",
            default="true",
            key=False,
            node_id="/testforms:toplevel/still-in-top/a-turned-on",
        ),
        call(
            ANY,
            "'false'",
            default="false",
            key=False,
            node_id="/testforms:toplevel/still-in-top/b-turned-on",
        ),
    ]

    # Assert Containers
    assert subject.callback_open_containing_node.mock_calls == [
        call(ANY, node_id="/testforms:toplevel", presence=True),
        call(ANY, node_id="/testforms:toplevel/mychoice/mycase1/box", presence=None),
        call(
            ANY,
            node_id="/testforms:toplevel/mychoice/mycase2/tupperware",
            presence=False,
        ),
        call(ANY, node_id="/testforms:toplevel/still-in-top", presence=False),
        call(ANY, presence=False, node_id="/testforms:toplevel/still-in-top/b"),
    ]

    # Assert List
    assert subject.callback_open_list.mock_calls == [
        call(ANY, count=2, node_id="/testforms:toplevel/simplelist")
    ]

    # Assert List Element
    assert subject.callback_open_list_element.mock_calls == [
        call(
            ANY,
            node_id="/testforms:toplevel/simplelist[simplekey='A']",
            key_values=[("simplekey", "A")],
            empty_list_element=False,
        ),
        call(
            ANY,
            node_id="/testforms:toplevel/simplelist[simplekey='B']",
            key_values=[("simplekey", "B")],
            empty_list_element=False,
        ),
    ]

    # Assert Choice
    assert subject.callback_open_choice.mock_calls == [
        call(ANY, node_id="/testforms:toplevel/mychoice")
    ]
    # Assert Case
    assert subject.callback_open_choice.mock_calls == [
        call(ANY, node_id="/testforms:toplevel/mychoice")
    ]
