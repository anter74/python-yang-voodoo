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


def write_string_based_asserts(subject, mock_object):
    i = 0
    with open("/tmp/t.txt", "w") as fh:
        for mock_call in getattr(subject, mock_object).mock_calls:
            fh.write(
                f'assert (\n    str(subject.{mock_object}.mock_calls[{i}])\n     == """{str(mock_call)}"""\n    )\n'
            )
            i += 1
        fh.write(f"assert len(subject.{mock_object}.mock_calls) == {i}")


@pytest.fixture
def subject(mocker):
    return TestExpander("testforms", Mock())


def test_leafs(subject):
    subject.process(open("templates/forms/simpleleaf.xml").read())

    # Assert Leafs
    # write_string_based_asserts(subject, "callback_write_leaf")
    assert (
        str(subject.callback_write_leaf.mock_calls[0])
        == """call(<libyang.schema.Leaf: simpleleaf string>, '', "'", False, default=None, key=False, template=False, node_id='/testforms:simpleleaf')"""
    )
    assert (
        str(subject.callback_write_leaf.mock_calls[1])
        == """call(<libyang.schema.Leaf: topdrop enumeration>, '', "'", False, default=None, key=False, template=False, node_id='/testforms:topdrop')"""
    )
    assert (
        str(subject.callback_write_leaf.mock_calls[2])
        == """call(<libyang.schema.Leaf: topleaf union>, '', "'", False, default=None, key=False, template=False, node_id='/testforms:topleaf')"""
    )
    assert (
        str(subject.callback_write_leaf.mock_calls[3])
        == """call(<libyang.schema.Leaf: hello string>, 'world', "'", True, default='put something here', key=False, template=False, node_id='/testforms:toplevel/hello')"""
    )
    assert (
        str(subject.callback_write_leaf.mock_calls[4])
        == """call(<libyang.schema.Leaf: animal animals>, 'bear', "'", True, default='bear', key=False, template=False, node_id='/testforms:toplevel/animal')"""
    )
    assert (
        str(subject.callback_write_leaf.mock_calls[5])
        == """call(<libyang.schema.Leaf: otheranimal animals>, 'bear', "'", True, default='bear', key=False, template=False, node_id='/testforms:toplevel/otheranimal')"""
    )
    assert (
        str(subject.callback_write_leaf.mock_calls[6])
        == """call(<libyang.schema.Leaf: tickbox boolean>, True, '"', True, default='true', key=False, template=False, node_id='/testforms:toplevel/tickbox')"""
    )
    assert (
        str(subject.callback_write_leaf.mock_calls[7])
        == """call(<libyang.schema.Leaf: thing-that-means-something empty>, '', "'", False, default=None, key=False, template=False, node_id='/testforms:toplevel/thing-that-means-something')"""
    )
    assert (
        str(subject.callback_write_leaf.mock_calls[8])
        == """call(<libyang.schema.Leaf: clown string>, '', "'", False, default=None, key=False, template=False, node_id='/testforms:toplevel/mychoice/mycase1/box/clown')"""
    )
    assert (
        str(subject.callback_write_leaf.mock_calls[9])
        == """call(<libyang.schema.Leaf: empty empty>, '', "'", False, default=None, key=False, template=False, node_id='/testforms:toplevel/mychoice/mycase3/empty')"""
    )
    assert (
        str(subject.callback_write_leaf.mock_calls[10])
        == """call(<libyang.schema.Leaf: simplekey string>, '', "'", False, default=None, key=True, template=False, node_id='/testforms:toplevel/simplelist/simplekey')"""
    )
    assert (
        str(subject.callback_write_leaf.mock_calls[11])
        == """call(<libyang.schema.Leaf: simplenonkey union>, 'non key value goes here', "'", False, default='non key value goes here', key=False, template=False, node_id='/testforms:toplevel/simplelist/simplenonkey')"""
    )
    assert (
        str(subject.callback_write_leaf.mock_calls[12])
        == """call(<libyang.schema.Leaf: of-the-world string>, 'withdefault', "'", False, default='withdefault', key=False, template=False, node_id='/testforms:toplevel/still-in-top/of-the-world')"""
    )
    assert (
        str(subject.callback_write_leaf.mock_calls[13])
        == """call(<libyang.schema.Leaf: pointer leafref>, '', "'", False, default=None, key=False, template=False, node_id='/testforms:toplevel/still-in-top/pointer')"""
    )
    assert (
        str(subject.callback_write_leaf.mock_calls[14])
        == """call(<libyang.schema.Leaf: a string>, '', "'", False, default=None, key=False, template=False, node_id='/testforms:toplevel/still-in-top/a')"""
    )
    assert (
        str(subject.callback_write_leaf.mock_calls[15])
        == """call(<libyang.schema.Leaf: a-turned-on boolean>, 'true', "'", False, default='true', key=False, template=False, node_id='/testforms:toplevel/still-in-top/a-turned-on')"""
    )
    assert (
        str(subject.callback_write_leaf.mock_calls[16])
        == """call(<libyang.schema.Leaf: b-turned-on boolean>, 'false', "'", False, default='false', key=False, template=False, node_id='/testforms:toplevel/still-in-top/b-turned-on')"""
    )
    assert (
        str(subject.callback_write_leaf.mock_calls[17])
        == """call(<libyang.schema.Leaf: foreign string>, '', "'", False, default=None, key=False, template=False, node_id='/testforms:other/foreign')"""
    )
    assert (
        str(subject.callback_write_leaf.mock_calls[18])
        == """call(<libyang.schema.Leaf: vacant empty>, '', "'", False, default=None, key=False, template=False, node_id='/testforms:other/vacant')"""
    )
    assert (
        str(subject.callback_write_leaf.mock_calls[19])
        == """call(<libyang.schema.Leaf: mainkey string>, '', "'", False, default=None, key=True, template=False, node_id='/testforms:mainlist/mainkey')"""
    )
    assert (
        str(subject.callback_write_leaf.mock_calls[20])
        == """call(<libyang.schema.Leaf: subkey string>, '', "'", False, default=None, key=True, template=False, node_id='/testforms:mainlist/subkey')"""
    )
    assert (
        str(subject.callback_write_leaf.mock_calls[21])
        == """call(<libyang.schema.Leaf: this string>, '', "'", False, default=None, key=False, template=False, node_id='/testforms:mainlist/another-choice/this/this')"""
    )
    assert (
        str(subject.callback_write_leaf.mock_calls[22])
        == """call(<libyang.schema.Leaf: key string>, '', "'", False, default=None, key=True, template=False, node_id='/testforms:mainlist/another-choice/this/this-second-list/key')"""
    )
    assert (
        str(subject.callback_write_leaf.mock_calls[23])
        == """call(<libyang.schema.Leaf: eating frankie>, '', "'", False, default=None, key=False, template=False, node_id='/testforms:mainlist/another-choice/this/this-second-list/monsters/eating/people/eating')"""
    )
    assert (
        str(subject.callback_write_leaf.mock_calls[24])
        == """call(<libyang.schema.Leaf: that string>, '', "'", False, default=None, key=False, template=False, node_id='/testforms:mainlist/another-choice/that/that')"""
    )
    assert (
        str(subject.callback_write_leaf.mock_calls[25])
        == """call(<libyang.schema.Leaf: key string>, '', "'", False, default=None, key=True, template=False, node_id='/testforms:mainlist/another-choice/that/that-second-list/key')"""
    )
    assert (
        str(subject.callback_write_leaf.mock_calls[26])
        == """call(<libyang.schema.Leaf: mainleaf string>, '', "'", False, default=None, key=False, template=False, node_id='/testforms:mainlist/maincontainer/mainleaf')"""
    )
    assert (
        str(subject.callback_write_leaf.mock_calls[27])
        == """call(<libyang.schema.Leaf: key1 string>, '', "'", False, default=None, key=True, template=False, node_id='/testforms:trio-list/key1')"""
    )
    assert (
        str(subject.callback_write_leaf.mock_calls[28])
        == """call(<libyang.schema.Leaf: key2 enumeration>, '', "'", False, default=None, key=True, template=False, node_id='/testforms:trio-list/key2')"""
    )
    assert (
        str(subject.callback_write_leaf.mock_calls[29])
        == """call(<libyang.schema.Leaf: key3 uint16>, '', "'", False, default=None, key=True, template=False, node_id='/testforms:trio-list/key3')"""
    )
    assert (
        str(subject.callback_write_leaf.mock_calls[30])
        == """call(<libyang.schema.Leaf: bob string>, '', "'", False, default=None, key=False, template=False, node_id='/testforms:trio-list/bob')"""
    )
    assert (
        str(subject.callback_write_leaf.mock_calls[31])
        == """call(<libyang.schema.Leaf: alice enumeration>, '', "'", False, default=None, key=False, template=False, node_id='/testforms:trio-list/alice')"""
    )
    assert (
        str(subject.callback_write_leaf.mock_calls[32])
        == """call(<libyang.schema.Leaf: mandatory uint32>, '', "'", False, default=None, key=False, template=False, node_id='/testforms:validation/mandatory')"""
    )
    assert (
        str(subject.callback_write_leaf.mock_calls[33])
        == """call(<libyang.schema.Leaf: this-is-a-thing string>, '', "'", False, default=None, key=False, template=False, node_id='/testforms:validation/sometimes/this-is-a-thing')"""
    )
    assert (
        str(subject.callback_write_leaf.mock_calls[34])
        == """call(<libyang.schema.Leaf: always boolean>, '', "'", False, default=None, key=False, template=False, node_id='/testforms:validation/always')"""
    )
    assert (
        str(subject.callback_write_leaf.mock_calls[35])
        == """call(<libyang.schema.Leaf: combo combotype>, '', "'", False, default=None, key=False, template=False, node_id='/testforms:validation/combo')"""
    )
    assert (
        str(subject.callback_write_leaf.mock_calls[36])
        == """call(<libyang.schema.Leaf: t1 string>, '', "'", False, default=None, key=False, template=False, node_id='/testforms:tab9/t1')"""
    )
    assert (
        str(subject.callback_write_leaf.mock_calls[37])
        == """call(<libyang.schema.Leaf: t2 boolean>, '', "'", False, default=None, key=False, template=False, node_id='/testforms:tab9/t2')"""
    )
    assert (
        str(subject.callback_write_leaf.mock_calls[38])
        == """call(<libyang.schema.Leaf: t3 empty>, '', "'", False, default=None, key=False, template=False, node_id='/testforms:tab9/t3')"""
    )
    assert (
        str(subject.callback_write_leaf.mock_calls[39])
        == """call(<libyang.schema.Leaf: t4 uint32>, '', "'", False, default=None, key=False, template=False, node_id='/testforms:tab9/t4')"""
    )
    assert (
        str(subject.callback_write_leaf.mock_calls[40])
        == """call(<libyang.schema.Leaf: t5 string>, '', "'", False, default=None, key=False, template=False, node_id='/testforms:tab9/t5')"""
    )
    assert (
        str(subject.callback_write_leaf.mock_calls[41])
        == """call(<libyang.schema.Leaf: t6 enumeration>, '', "'", False, default=None, key=False, template=False, node_id='/testforms:tab9/t6')"""
    )
    assert (
        str(subject.callback_write_leaf.mock_calls[42])
        == """call(<libyang.schema.Leaf: t1 string>, '', "'", False, default=None, key=False, template=False, node_id='/testforms:tab11/t1')"""
    )
    assert (
        str(subject.callback_write_leaf.mock_calls[43])
        == """call(<libyang.schema.Leaf: t2 boolean>, '', "'", False, default=None, key=False, template=False, node_id='/testforms:tab11/t2')"""
    )
    assert (
        str(subject.callback_write_leaf.mock_calls[44])
        == """call(<libyang.schema.Leaf: t3 empty>, '', "'", False, default=None, key=False, template=False, node_id='/testforms:tab11/t3')"""
    )
    assert (
        str(subject.callback_write_leaf.mock_calls[45])
        == """call(<libyang.schema.Leaf: t4 uint32>, '', "'", False, default=None, key=False, template=False, node_id='/testforms:tab11/t4')"""
    )
    assert (
        str(subject.callback_write_leaf.mock_calls[46])
        == """call(<libyang.schema.Leaf: t5 string>, '', "'", False, default=None, key=False, template=False, node_id='/testforms:tab11/t5')"""
    )
    assert (
        str(subject.callback_write_leaf.mock_calls[47])
        == """call(<libyang.schema.Leaf: t6 enumeration>, '', "'", False, default=None, key=False, template=False, node_id='/testforms:tab11/t6')"""
    )
    assert len(subject.callback_write_leaf.mock_calls) == 48

    # Assert Leaf-Lists
    # write_string_based_asserts(subject, "callback_write_leaflist_item")
    assert len(subject.callback_write_leaflist_item.mock_calls) == 0

    # Assert Containers
    # write_string_based_asserts(subject, "callback_open_containing_node")
    assert (
        str(subject.callback_open_containing_node.mock_calls[0])
        == """call(<libyang.schema.Container: toplevel>, presence=True, node_id='/testforms:toplevel')"""
    )
    assert (
        str(subject.callback_open_containing_node.mock_calls[1])
        == """call(<libyang.schema.Container: box>, presence=None, node_id='/testforms:toplevel/mychoice/mycase1/box')"""
    )
    assert (
        str(subject.callback_open_containing_node.mock_calls[2])
        == """call(<libyang.schema.Container: tupperware>, presence=False, node_id='/testforms:toplevel/mychoice/mycase2/tupperware')"""
    )
    assert (
        str(subject.callback_open_containing_node.mock_calls[3])
        == """call(<libyang.schema.Container: still-in-top>, presence=False, node_id='/testforms:toplevel/still-in-top')"""
    )
    assert (
        str(subject.callback_open_containing_node.mock_calls[4])
        == """call(<libyang.schema.Container: b>, presence=False, node_id='/testforms:toplevel/still-in-top/b')"""
    )
    assert (
        str(subject.callback_open_containing_node.mock_calls[5])
        == """call(<libyang.schema.Container: other>, presence=False, node_id='/testforms:other')"""
    )
    assert (
        str(subject.callback_open_containing_node.mock_calls[6])
        == """call(<libyang.schema.Container: monsters>, presence=None, node_id='/testforms:mainlist/another-choice/this/this-second-list/monsters')"""
    )
    assert (
        str(subject.callback_open_containing_node.mock_calls[7])
        == """call(<libyang.schema.Container: eating>, presence=None, node_id='/testforms:mainlist/another-choice/this/this-second-list/monsters/eating')"""
    )
    assert (
        str(subject.callback_open_containing_node.mock_calls[8])
        == """call(<libyang.schema.Container: people>, presence=None, node_id='/testforms:mainlist/another-choice/this/this-second-list/monsters/eating/people')"""
    )
    assert (
        str(subject.callback_open_containing_node.mock_calls[9])
        == """call(<libyang.schema.Container: maincontainer>, presence=False, node_id='/testforms:mainlist/maincontainer')"""
    )
    assert (
        str(subject.callback_open_containing_node.mock_calls[10])
        == """call(<libyang.schema.Container: validation>, presence=False, node_id='/testforms:validation')"""
    )
    assert (
        str(subject.callback_open_containing_node.mock_calls[11])
        == """call(<libyang.schema.Container: sometimes>, presence=None, node_id='/testforms:validation/sometimes')"""
    )
    assert (
        str(subject.callback_open_containing_node.mock_calls[12])
        == """call(<libyang.schema.Container: tab9>, presence=False, node_id='/testforms:tab9')"""
    )
    assert (
        str(subject.callback_open_containing_node.mock_calls[13])
        == """call(<libyang.schema.Container: tab10>, presence=None, node_id='/testforms:tab10')"""
    )
    assert (
        str(subject.callback_open_containing_node.mock_calls[14])
        == """call(<libyang.schema.Container: tab11>, presence=None, node_id='/testforms:tab11')"""
    )
    assert len(subject.callback_open_containing_node.mock_calls) == 15

    # Assert List
    # write_string_based_asserts(subject, "callback_open_list")
    assert (
        str(subject.callback_open_list.mock_calls[0])
        == """call(<libyang.schema.List: simplelist [simplekey]>, count=0, node_id='/testforms:toplevel/simplelist')"""
    )
    assert (
        str(subject.callback_open_list.mock_calls[1])
        == """call(<libyang.schema.List: mainlist [mainkey, subkey]>, count=0, node_id='/testforms:mainlist')"""
    )
    assert (
        str(subject.callback_open_list.mock_calls[2])
        == """call(<libyang.schema.List: this-second-list [key]>, count=0, node_id='/testforms:mainlist/another-choice/this/this-second-list')"""
    )
    assert (
        str(subject.callback_open_list.mock_calls[3])
        == """call(<libyang.schema.List: that-second-list [key]>, count=0, node_id='/testforms:mainlist/another-choice/that/that-second-list')"""
    )
    assert (
        str(subject.callback_open_list.mock_calls[4])
        == """call(<libyang.schema.List: trio-list [key1, key2, key3]>, count=0, node_id='/testforms:trio-list')"""
    )
    assert len(subject.callback_open_list.mock_calls) == 5

    # Assert List Element
    # write_string_based_asserts(subject, "callback_open_list_element")
    assert (
        str(subject.callback_open_list_element.mock_calls[0])
        == """call(<libyang.schema.List: simplelist [simplekey]>, key_values=[('simplekey', None)], empty_list_element=True, force_open=False, node_id='/testforms:toplevel/simplelist')"""
    )
    assert (
        str(subject.callback_open_list_element.mock_calls[1])
        == """call(<libyang.schema.List: mainlist [mainkey, subkey]>, key_values=[('mainkey', None), ('subkey', None)], empty_list_element=True, force_open=False, node_id='/testforms:mainlist')"""
    )
    assert (
        str(subject.callback_open_list_element.mock_calls[2])
        == """call(<libyang.schema.List: this-second-list [key]>, key_values=[('key', None)], empty_list_element=True, force_open=False, node_id='/testforms:mainlist/another-choice/this/this-second-list')"""
    )
    assert (
        str(subject.callback_open_list_element.mock_calls[3])
        == """call(<libyang.schema.List: that-second-list [key]>, key_values=[('key', None)], empty_list_element=True, force_open=False, node_id='/testforms:mainlist/another-choice/that/that-second-list')"""
    )
    assert (
        str(subject.callback_open_list_element.mock_calls[4])
        == """call(<libyang.schema.List: trio-list [key1, key2, key3]>, key_values=[('key1', None), ('key2', None), ('key3', None)], empty_list_element=True, force_open=False, node_id='/testforms:trio-list')"""
    )
    assert len(subject.callback_open_list_element.mock_calls) == 5

    # Assert Choice
    # write_string_based_asserts(subject, "callback_open_choice")
    assert (
        str(subject.callback_open_choice.mock_calls[0])
        == """call(<libyang.schema.Node: mychoice>, node_id='/testforms:toplevel/mychoice')"""
    )
    assert (
        str(subject.callback_open_choice.mock_calls[1])
        == """call(<libyang.schema.Node: another-choice>, node_id='/testforms:mainlist/another-choice')"""
    )
    assert len(subject.callback_open_choice.mock_calls) == 2

    # Assert Case
    # write_string_based_asserts(subject, "callback_open_case")
    assert (
        str(subject.callback_open_case.mock_calls[0])
        == """call(<libyang.schema.Node: mycase1>, False, True, node_id='/testforms:toplevel/mychoice/mycase1')"""
    )
    assert (
        str(subject.callback_open_case.mock_calls[1])
        == """call(<libyang.schema.Node: mycase2>, False, True, node_id='/testforms:toplevel/mychoice/mycase2')"""
    )
    assert (
        str(subject.callback_open_case.mock_calls[2])
        == """call(<libyang.schema.Node: mycase3>, False, True, node_id='/testforms:toplevel/mychoice/mycase3')"""
    )
    assert (
        str(subject.callback_open_case.mock_calls[3])
        == """call(<libyang.schema.Node: this>, False, True, node_id='/testforms:mainlist/another-choice/this')"""
    )
    assert (
        str(subject.callback_open_case.mock_calls[4])
        == """call(<libyang.schema.Node: that>, False, True, node_id='/testforms:mainlist/another-choice/that')"""
    )
    assert len(subject.callback_open_case.mock_calls) == 5
