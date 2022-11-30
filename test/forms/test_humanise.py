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
    return TestExpander("integrationtest", Mock())


def test_humanising_types(subject):
    node = list(
        subject.ctx.find_path(
            "/integrationtest:morecomplex/integrationtest:inner/integrationtest:leaf8"
        )
    )[0]

    # Assert Union of Union's
    assert list(subject.get_human_types(node)) == [
        ("type2 (uint32)", []),
        ("enumeration [ A; B; C ]", []),
        ("type5 (string)", []),
    ]


def test_humanising_constraints_patterns_and_lengths(subject):
    node = list(
        subject.ctx.find_path(
            "/integrationtest:validator/integrationtest:strings/integrationtest:patternandlengtherror"
        )
    )[0]

    # Assert Leaf Ref's
    assert list(subject.get_human_constraints(node.type())) == [
        "Pattern: A.+Z",
        "Length: 2 | 3",
    ]


def test_humanising_constraints_ranges(subject):
    node = list(
        subject.ctx.find_path(
            "/integrationtest:morecomplex/integrationtest:inner/integrationtest:uint8keylist/integrationtest:mykey"
        )
    )[0]

    # Assert Leaf Ref's
    assert list(subject.get_human_constraints(node.type())) == ["Range: 0..7"]
