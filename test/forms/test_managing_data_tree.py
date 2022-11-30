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


def test_retrieve_a_list_element(subject):
    subject.load(open("templates/forms/simplelist2.xml").read())

    # Act
    subject.subprocess("/testforms:toplevel/simplelist[simplekey='B']")

    assert subject.callback_open_list.mock_calls == [
        # call(ANY, count=2, node_id="/testforms:toplevel/simplelist")
    ]
    assert subject.callback_open_list_element.mock_calls == [
        call(
            ANY,
            key_values=[("simplekey", "B")],
            empty_list_element=False,
            node_id="/testforms:toplevel/simplelist[simplekey='B']",
        )
    ]
    assert subject.callback_write_leaf.mock_calls == [
        call(
            ANY,
            "'B'",
            default=None,
            key=True,
            node_id="/testforms:toplevel/simplelist[simplekey='B']/simplekey",
        ),
        call(
            ANY,
            "'non key value goes here'",
            default="non key value goes here",
            key=False,
            node_id="/testforms:toplevel/simplelist[simplekey='B']/simplenonkey",
        ),
    ]
    assert subject.callback_open_choice.mock_calls == []
    assert subject.callback_open_case.mock_calls == []
    assert subject.callback_open_containing_node.mock_calls == []


def test_add_a_list_element(subject):
    subject.load(open("templates/forms/simplelist2.xml").read())

    # Act
    subject.data_tree_add_list_element(
        "/testforms:toplevel/simplelist", (("simplekey", "C"),)
    )
    subject.data_tree_set_leaf(
        "/testforms:toplevel/simplelist[simplekey='C']/simplenonkey",
        "cult-of-dom-keller",
    )
    subject.subprocess("/testforms:toplevel/simplelist[simplekey='C']")

    assert subject.callback_open_list.mock_calls == [
        # call(ANY, count=2, node_id="/testforms:toplevel/simplelist")
    ]
    assert subject.callback_open_list_element.mock_calls == [
        call(
            ANY,
            key_values=[("simplekey", "C")],
            empty_list_element=False,
            node_id="/testforms:toplevel/simplelist[simplekey='C']",
        )
    ]
    assert subject.callback_write_leaf.mock_calls == [
        call(
            ANY,
            "'C'",
            default=None,
            key=True,
            node_id="/testforms:toplevel/simplelist[simplekey='C']/simplekey",
        ),
        call(
            ANY,
            "'cult-of-dom-keller'",
            default="non key value goes here",
            key=False,
            node_id="/testforms:toplevel/simplelist[simplekey='C']/simplenonkey",
        ),
    ]
    assert subject.callback_open_choice.mock_calls == []
    assert subject.callback_open_case.mock_calls == []
    assert subject.callback_open_containing_node.mock_calls == []


def test_remove_a_leaf_of_a_list_element(subject):
    subject.load(open("templates/forms/simplelist4.xml").read())

    subject.subprocess("/testforms:toplevel/simplelist[simplekey='B']")

    assert subject.callback_open_list.mock_calls == []
    assert subject.callback_open_list_element.mock_calls == [
        call(
            ANY,
            key_values=[("simplekey", "B")],
            empty_list_element=False,
            node_id="/testforms:toplevel/simplelist[simplekey='B']",
        )
    ]
    assert subject.callback_write_leaf.mock_calls == [
        call(
            ANY,
            "'B'",
            default=None,
            key=True,
            node_id="/testforms:toplevel/simplelist[simplekey='B']/simplekey",
        ),
        call(
            ANY,
            "'brian-jonestown-massacre'",
            default="non key value goes here",
            key=False,
            node_id="/testforms:toplevel/simplelist[simplekey='B']/simplenonkey",
        ),
    ]
    assert subject.callback_open_choice.mock_calls == []
    assert subject.callback_open_case.mock_calls == []
    assert subject.callback_open_containing_node.mock_calls == []

    subject.callback_write_leaf = Mock()

    # Act
    subject.data_tree_set_leaf(
        "/testforms:toplevel/simplelist[simplekey='B']/simplenonkey", None
    )

    subject.subprocess("/testforms:toplevel/simplelist[simplekey='B']")

    # Assert
    assert subject.callback_write_leaf.mock_calls == [
        call(
            ANY,
            "'B'",
            default=None,
            key=True,
            node_id="/testforms:toplevel/simplelist[simplekey='B']/simplekey",
        ),
        call(
            ANY,
            "'non key value goes here'",
            default="non key value goes here",
            key=False,
            node_id="/testforms:toplevel/simplelist[simplekey='B']/simplenonkey",
        ),
    ]


def test_trying_to_subprocess_a_non_list_element(subject):
    subject.load(open("templates/forms/simplelist2.xml").read())

    # Act
    with pytest.raises(NotImplementedError) as err:
        subject.subprocess("/testforms:toplevel")

    assert (
        str(err.value)
        == "subprocess only supports processing of a list element: /testforms:toplevel"
    )
