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
        self.callback_write_leaflist_item = Mock()
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
            template=False,
            node_id="/testforms:simpleleaf",
        ),
        call(
            ANY,
            "",
            "'",
            False,
            default=None,
            key=False,
            template=False,
            node_id="/testforms:topleaf",
        ),
        call(
            ANY,
            "world",
            "'",
            True,
            default="put something here",
            key=False,
            template=False,
            node_id="/testforms:toplevel/hello",
        ),
        call(
            ANY,
            "",
            "'",
            False,
            default=None,
            key=False,
            template=False,
            node_id="/testforms:toplevel/mychoice/mycase1/box/clown",
        ),
        call(
            ANY,
            "",
            "'",
            False,
            default=None,
            key=False,
            template=False,
            node_id="/testforms:toplevel/mychoice/mycase3/empty",
        ),
        call(
            ANY,
            "withdefault",
            "'",
            False,
            default="withdefault",
            key=False,
            template=False,
            node_id="/testforms:toplevel/still-in-top/of-the-world",
        ),
        call(
            ANY,
            "",
            "'",
            False,
            default=None,
            key=False,
            template=False,
            node_id="/testforms:toplevel/still-in-top/pointer",
        ),
        call(
            ANY,
            "",
            "'",
            False,
            default=None,
            key=False,
            template=False,
            node_id="/testforms:toplevel/still-in-top/a",
        ),
        call(
            ANY,
            True,
            '"',
            False,
            default=True,
            key=False,
            template=False,
            node_id="/testforms:toplevel/still-in-top/a-turned-on",
        ),
        call(
            ANY,
            False,
            '"',
            False,
            default=False,
            key=False,
            template=False,
            node_id="/testforms:toplevel/still-in-top/b-turned-on",
        ),
        call(
            ANY,
            "",
            "'",
            False,
            default=None,
            key=False,
            template=False,
            node_id="/testforms:other/foreign",
        ),
        call(
            ANY,
            "",
            "'",
            False,
            default=None,
            key=False,
            template=False,
            node_id="/testforms:other/vacant",
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
            node_id="/testforms:toplevel/mychoice/mycase2/tupperware",
            presence=False,
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
    ]

    # Assert List Element
    assert subject.callback_open_list_element.mock_calls == []

    # Assert Choice
    assert subject.callback_open_choice.mock_calls == [
        call(
            ANY,
            node_id="/testforms:toplevel/mychoice",
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
    ]


def test_leaf_lists(subject):
    subject.process(open("templates/forms/simplelist4.xml").read())

    # Assert Leafs
    assert subject.callback_write_leaf.mock_calls == [
        call(
            ANY,
            "",
            "'",
            False,
            default=None,
            key=False,
            template=False,
            node_id="/testforms:simpleleaf",
        ),
        call(
            ANY,
            "",
            "'",
            False,
            default=None,
            key=False,
            template=False,
            node_id="/testforms:topleaf",
        ),
        call(
            ANY,
            "world",
            "'",
            True,
            default="put something here",
            key=False,
            template=False,
            node_id="/testforms:toplevel/hello",
        ),
        call(
            ANY,
            "",
            "'",
            False,
            default=None,
            key=False,
            template=False,
            node_id="/testforms:toplevel/mychoice/mycase1/box/clown",
        ),
        call(
            ANY,
            "",
            "'",
            False,
            default=None,
            key=False,
            template=False,
            node_id="/testforms:toplevel/mychoice/mycase3/empty",
        ),
        call(
            ANY,
            "A",
            "'",
            True,
            default=None,
            key=True,
            template=False,
            node_id="/testforms:toplevel/simplelist[simplekey='A']/simplekey",
        ),
        call(
            ANY,
            "non key value goes here",
            "'",
            True,  # is there special behaviour for default leaves in lists?
            default="non key value goes here",
            key=False,
            template=False,
            node_id="/testforms:toplevel/simplelist[simplekey='A']/simplenonkey",
        ),
        call(
            ANY,
            "B",
            "'",
            True,
            default=None,
            key=True,
            template=False,
            node_id="/testforms:toplevel/simplelist[simplekey='B']/simplekey",
        ),
        call(
            ANY,
            "brian-jonestown-massacre",
            "'",
            True,
            default="non key value goes here",
            key=False,
            template=False,
            node_id="/testforms:toplevel/simplelist[simplekey='B']/simplenonkey",
        ),
        call(
            ANY,
            "withdefault",
            "'",
            False,
            default="withdefault",
            key=False,
            template=False,
            node_id="/testforms:toplevel/still-in-top/of-the-world",
        ),
        call(
            ANY,
            "",
            "'",
            False,
            default=None,
            key=False,
            template=False,
            node_id="/testforms:toplevel/still-in-top/pointer",
        ),
        call(
            ANY,
            "",
            "'",
            False,
            default=None,
            key=False,
            template=False,
            node_id="/testforms:toplevel/still-in-top/a",
        ),
        call(
            ANY,
            True,
            '"',
            False,
            default=True,
            key=False,
            template=False,
            node_id="/testforms:toplevel/still-in-top/a-turned-on",
        ),
        call(
            ANY,
            False,
            '"',
            False,
            default=False,
            key=False,
            template=False,
            node_id="/testforms:toplevel/still-in-top/b-turned-on",
        ),
        call(
            ANY,
            "",
            "'",
            False,
            default=None,
            key=False,
            template=False,
            node_id="/testforms:other/foreign",
        ),
        call(
            ANY,
            "",
            "'",
            False,
            default=None,
            key=False,
            template=False,
            node_id="/testforms:other/vacant",
        ),
    ]

    # Assert Leaf-Lists
    assert subject.callback_open_leaflist.mock_calls == [
        call(
            ANY,
            count=2,
            node_id="/testforms:toplevel/multi",
        )
    ]
    assert subject.callback_write_leaflist_item.mock_calls == [
        call(
            ANY,
            "m",
            "'",
            True,
            node_id="/testforms:toplevel/multi[.='m']",
            template=False,
        ),
        call(
            ANY,
            "M",
            "'",
            True,
            node_id="/testforms:toplevel/multi[.='M']",
            template=False,
        ),
    ]

    # Assert Containers
    assert subject.callback_open_containing_node.mock_calls == [
        call(ANY, presence=True, node_id="/testforms:toplevel"),
        call(ANY, presence=None, node_id="/testforms:toplevel/mychoice/mycase1/box"),
        call(ANY, presence=True, node_id="/testforms:toplevel/mychoice/mycase2/tupperware"),
        call(ANY, presence=False, node_id="/testforms:toplevel/still-in-top"),
        call(ANY, presence=False, node_id="/testforms:toplevel/still-in-top/b"),
        call(ANY, presence=False, node_id="/testforms:other"),
    ]

    # Assert List
    assert subject.callback_open_list.mock_calls == [
        call(ANY, count=2, node_id="/testforms:toplevel/simplelist"),
        call(ANY, count=0, node_id="/testforms:mainlist"),
    ]

    # Assert List Element
    assert subject.callback_open_list_element.mock_calls == [
        call(
            ANY,
            key_values=[("simplekey", "A")],
            empty_list_element=False,
            node_id="/testforms:toplevel/simplelist[simplekey='A']",
        ),
        call(
            ANY,
            key_values=[("simplekey", "B")],
            empty_list_element=False,
            node_id="/testforms:toplevel/simplelist[simplekey='B']",
        ),
    ]

    # Assert Choice
    assert subject.callback_open_choice.mock_calls == [
        call(
            ANY,
            node_id="/testforms:toplevel/mychoice",
        ),
    ]

    # Assert Case
    assert subject.callback_open_case.mock_calls == [
        call(
            ANY,
            False,
            False,
            node_id="/testforms:toplevel/mychoice/mycase1",
        ),
        call(
            ANY,
            True,
            False,
            node_id="/testforms:toplevel/mychoice/mycase2",
        ),
        call(
            ANY,
            False,
            False,
            node_id="/testforms:toplevel/mychoice/mycase3",
        ),
    ]
