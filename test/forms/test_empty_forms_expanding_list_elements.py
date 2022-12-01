import libyang
import pytest
from mock import Mock, call, ANY

from yangvoodoo.SchemaData import Expander


class TestExpander(Expander):
    INCLUDE_BLANK_LIST_ELEMENTS = True

    def __init__(self, yang_module, log):
        super().__init__(yang_module, log)
        self.callback_open_containing_node = Mock()
        self.callback_close_containing_node = Mock()
        self.callback_write_leaf = Mock()
        self.callback_open_leaflist = Mock()
        self.callback_close_leaflist = Mock()
        self.callback_write_leaflist_item = Mock()
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


def test_leafs(subject):
    subject.process(open("templates/forms/simpleleaf.xml").read())

    # Assert Leafs
    assert subject.callback_write_leaf.mock_calls == [
        call(
            ANY,
            "",
            "'",
            False,
            default=None,
            key=False,
            node_id="/testforms:topleaf",
        ),
        call(
            ANY,
            "world",
            "'",
            True,
            default="put something here",
            key=False,
            node_id="/testforms:toplevel/hello",
        ),
        call(
            ANY,
            "",
            "'",
            False,
            default=None,
            key=False,
            node_id="/testforms:toplevel/mychoice/mycase1/box/clown",
        ),
        call(
            ANY,
            "",
            "'",
            False,
            default=None,
            key=False,
            node_id="/testforms:toplevel/mychoice/mycase3/empty",
        ),
        call(
            ANY,
            "",
            "'",
            False,
            default=None,
            key=True,
            node_id="/testforms:toplevel/simplelist/simplekey",
        ),
        call(
            ANY,
            "non key value goes here",
            "'",
            False,
            default="non key value goes here",
            key=False,
            node_id="/testforms:toplevel/simplelist/simplenonkey",
        ),
        call(
            ANY,
            "withdefault",
            "'",
            False,
            default="withdefault",
            key=False,
            node_id="/testforms:toplevel/still-in-top/of-the-world",
        ),
        call(
            ANY,
            "",
            "'",
            False,
            default=None,
            key=False,
            node_id="/testforms:toplevel/still-in-top/pointer",
        ),
        call(
            ANY,
            "",
            "'",
            False,
            default=None,
            key=False,
            node_id="/testforms:toplevel/still-in-top/a",
        ),
        call(
            ANY,
            True,
            '"',
            False,
            default=True,
            key=False,
            node_id="/testforms:toplevel/still-in-top/a-turned-on",
        ),
        call(
            ANY,
            False,
            '"',
            False,
            default=False,
            key=False,
            node_id="/testforms:toplevel/still-in-top/b-turned-on",
        ),
        call(
            ANY,
            "",
            "'",
            False,
            default=None,
            key=False,
            node_id="/testforms:other/foreign",
        ),
        call(
            ANY,
            "",
            "'",
            False,
            default=None,
            key=False,
            node_id="/testforms:other/vacant",
        ),
        call(
            ANY,
            "",
            "'",
            False,
            default=None,
            key=True,
            node_id="/testforms:mainlist/mainkey",
        ),
        call(
            ANY,
            "",
            "'",
            False,
            default=None,
            key=True,
            node_id="/testforms:mainlist/subkey",
        ),
        call(
            ANY,
            "",
            "'",
            False,
            default=None,
            key=False,
            node_id="/testforms:mainlist/another-choice/this/this",
        ),
        call(
            ANY,
            "",
            "'",
            False,
            default=None,
            key=True,
            node_id="/testforms:mainlist/another-choice/this/this-second-list/key",
        ),
        call(
            ANY,
            "",
            "'",
            False,
            default=None,
            key=False,
            node_id="/testforms:mainlist/another-choice/that/that",
        ),
        call(
            ANY,
            "",
            "'",
            False,
            default=None,
            key=True,
            node_id="/testforms:mainlist/another-choice/that/that-second-list/key",
        ),
        call(
            ANY,
            "",
            "'",
            False,
            default=None,
            key=False,
            node_id="/testforms:mainlist/maincontainer/mainleaf",
        ),
    ]

    # Assert Leaf-Lists
    assert subject.callback_write_leaflist_item.mock_calls == []

    # Assert Containers
    assert subject.callback_open_containing_node.mock_calls == [
        call(
            ANY,
            presence=True,
            node_id="/testforms:toplevel",
        ),
        call(
            ANY,
            presence=None,
            node_id="/testforms:toplevel/mychoice/mycase1/box",
        ),
        call(
            ANY,
            presence=False,
            node_id="/testforms:toplevel/mychoice/mycase2/tupperware",
        ),
        call(
            ANY,
            presence=False,
            node_id="/testforms:toplevel/still-in-top",
        ),
        call(
            ANY,
            presence=False,
            node_id="/testforms:toplevel/still-in-top/b",
        ),
        call(
            ANY,
            presence=False,
            node_id="/testforms:other",
        ),
        call(
            ANY,
            presence=False,
            node_id="/testforms:mainlist/maincontainer",
        ),
    ]

    # Assert List
    assert subject.callback_open_list.mock_calls == [
        call(
            ANY,
            count=0,
            node_id="/testforms:toplevel/simplelist",
        ),
        call(
            ANY,
            count=0,
            node_id="/testforms:mainlist",
        ),
        call(
            ANY,
            count=0,
            node_id="/testforms:mainlist/another-choice/this/this-second-list",
        ),
        call(
            ANY,
            count=0,
            node_id="/testforms:mainlist/another-choice/that/that-second-list",
        ),
    ]

    # Assert List Element
    assert subject.callback_open_list_element.mock_calls == [
        call(
            ANY,
            key_values=[("simplekey", None)],
            node_id="/testforms:toplevel/simplelist",
            empty_list_element=True,
        ),
        call(
            ANY,
            key_values=[("mainkey", None), ("subkey", None)],
            empty_list_element=True,
            node_id="/testforms:mainlist",
        ),
        call(
            ANY,
            key_values=[("key", None)],
            empty_list_element=True,
            node_id="/testforms:mainlist/another-choice/this/this-second-list",
        ),
        call(
            ANY,
            key_values=[("key", None)],
            empty_list_element=True,
            node_id="/testforms:mainlist/another-choice/that/that-second-list",
        ),
    ]

    # Assert Choice
    assert subject.callback_open_choice.mock_calls == [
        call(
            ANY,
            node_id="/testforms:toplevel/mychoice",
        ),
        call(
            ANY,
            node_id="/testforms:mainlist/another-choice",
        ),
    ]

    # Assert Case
    assert subject.callback_open_case.mock_calls == [
        call(
            ANY,
            False,
            True,
            node_id="/testforms:toplevel/mychoice/mycase1",
        ),
        call(
            ANY,
            False,
            True,
            node_id="/testforms:toplevel/mychoice/mycase2",
        ),
        call(
            ANY,
            False,
            True,
            node_id="/testforms:toplevel/mychoice/mycase3",
        ),
        call(
            ANY,
            False,
            True,
            node_id="/testforms:mainlist/another-choice/this",
        ),
        call(
            ANY,
            False,
            True,
            node_id="/testforms:mainlist/another-choice/that",
        ),
    ]
