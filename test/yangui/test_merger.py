import json
import pytest

from mock import Mock

import libyang
import yangvoodoo
from yangvoodoo.Merger import DataTree, DataTreeChange, DataTreeChanges, InvalidChangeError
from yangvoodoo.Errors import InvalidPayloadError


def test_get_root_yang():
    assert (
        DataTree.get_root_yang_model({"testforms:topdrop": "b", "testforms:simpleleaf": "a", "testforms:topleaf": "a"})
        == "testforms"
    )

    with pytest.raises(InvalidPayloadError) as err:
        assert DataTree.get_root_yang_model({})
    assert str(err.value) == "Unable to determine yang model from payload."


def test_connect_yang():
    session = DataTree.connect_yang_model({"testforms:topdrop": "b"}, "testforms", "yang/")
    assert session.module == "testforms"
    assert isinstance(session, yangvoodoo.DataAccess)

    session = DataTree.connect_yang_model({"testforms:topdrop": "b"}, yang_location="yang")
    assert session.module == "testforms"
    assert isinstance(session, yangvoodoo.DataAccess)


def test_converting_json_to_datatree_changes():
    log = Mock()

    # Act
    result = list(
        DataTreeChanges.convert([{"base64_path": "L3Rlc3Rmb3Jtczp0YWI5L3Qx", "value": "bob", "action": "set"}], log)
    )

    # Assert
    assert len(result) == 1
    assert repr(result[0]) == "set: /testforms:tab9/t1 -> bob"

    # Act
    result = list(DataTreeChanges.convert([], log))

    # Assert
    assert len(result) == 0

    # Act
    with pytest.raises(InvalidChangeError) as err:
        list(DataTreeChanges.convert([{}], log))

    # Assert
    assert len(result) == 0


def test_merging():
    log = Mock()
    changes = [DataTreeChange(DataTreeChange.ACTION_SET, "/testforms:simpleleaf", "a")]

    # Act
    session, json_dict, changes = DataTree.process_data_tree_against_libyang(
        {"testforms:topdrop": "b"}, changes, yang_location="yang", log=log
    )

    # Assert
    assert (
        session.dumps()
        == '<topdrop xmlns="http://testforms">b</topdrop><simpleleaf xmlns="http://testforms">a</simpleleaf>'
    )
    assert json_dict == {"testforms:topdrop": "b", "testforms:simpleleaf": "a"}
    assert changes == []


def test_merging_violating_datatree_constraints():
    log = Mock()
    changes = [DataTreeChange(DataTreeChange.ACTION_SET, "/testforms:simpleleaf", "xxxxxxxa")]

    # Act
    with pytest.raises(libyang.util.InvalidSchemaOrValueError) as err:
        DataTree.process_data_tree_against_libyang({"testforms:topdrop": "b"}, changes, yang_location="yang", log=log)

    # Assert
    assert 'Value: "xxxxxxxa"' in str(err.value)
    assert "XPATH: /testforms:simpleleaf" in str(err.value)


def test_merging_full_set_example():
    log = Mock()
    changes = [
        DataTreeChange(DataTreeChange.ACTION_SET, "/testforms:simpleleaf", "a"),
        DataTreeChange(DataTreeChange.ACTION_SET_EMPTY, "/testforms:toplevel/thing-that-means-something", "on"),
        DataTreeChange(DataTreeChange.ACTION_SET_BOOLEAN, "/testforms:toplevel/tickbox", "on"),
        DataTreeChange(DataTreeChange.ACTION_SET, "/testforms:toplevel/hello", "world"),
        DataTreeChange(DataTreeChange.ACTION_SET, "/testforms:toplevel/hello", "world!"),
    ]

    # Act
    session, json_dict, changes = DataTree.process_data_tree_against_libyang(
        {"testforms:topdrop": "b"}, changes, yang_location="yang", log=log
    )
    session2 = yangvoodoo.DataAccess()
    session2.connect("testforms", "yang")
    session2.loads(session.dumps())
    root = session.get_node()

    # Assert
    assert root.simpleleaf == "a"
    assert root.toplevel.thing_that_means_something.exists() is True
    assert root.toplevel.tickbox is True
    assert root.toplevel.hello == "world!"


def test_merging_ensure_failures_are_supressed_until_the_end_and_cancelled_out():
    log = Mock()
    changes = [
        DataTreeChange(DataTreeChange.ACTION_SET, "/testforms:simpleleaf", "a"),
        DataTreeChange(DataTreeChange.ACTION_SET, "/testforms:simpleleaf", "b"),
        DataTreeChange(DataTreeChange.ACTION_SET, "/testforms:simpleleaf", "c"),
        DataTreeChange(DataTreeChange.ACTION_SET, "/testforms:simpleleaf", "d"),
        DataTreeChange(DataTreeChange.ACTION_SET, "/testforms:simpleleaf", "a"),
    ]

    # Act
    session, json_dict, changes = DataTree.process_data_tree_against_libyang(
        {"testforms:topdrop": "b"}, changes, yang_location="yang", log=log
    )
    session2 = yangvoodoo.DataAccess()
    session2.connect("testforms", "yang")
    session2.loads(session.dumps())
    root = session.get_node()

    # Assert
    assert root.simpleleaf == "a"


def test_merging_ensure_failures_are_supressed_until_the_end_and_raised():
    log = Mock()
    changes = [
        DataTreeChange(DataTreeChange.ACTION_SET, "/testforms:simpleleaf", "a"),
        DataTreeChange(DataTreeChange.ACTION_SET, "/testforms:simpleleaf", "b"),
        DataTreeChange(DataTreeChange.ACTION_SET, "/testforms:simpleleaf", "c"),
        DataTreeChange(DataTreeChange.ACTION_SET, "/testforms:simpleleaf", "d"),
    ]

    # Act
    with pytest.raises(libyang.util.LibyangError) as err:
        DataTree.process_data_tree_against_libyang({"testforms:topdrop": "b"}, changes, yang_location="yang", log=log)

    # Assert
    assert 'Value: "d"' in str(err.value)
    assert "XPATH: /testforms:simpleleaf" in str(err.value)


def test_merging_deleting_data():
    log = Mock()
    changes = [
        DataTreeChange(DataTreeChange.ACTION_SET, "/testforms:toplevel/hello", "world"),
        DataTreeChange(DataTreeChange.ACTION_DELETE, "/testforms:toplevel/hello", ""),
    ]

    # Act
    session, json_dict, changes = DataTree.process_data_tree_against_libyang(
        {"testforms:topdrop": "b"}, changes, yang_location="yang", log=log
    )
    session2 = yangvoodoo.DataAccess()
    session2.connect("testforms", "yang")
    session2.loads(session.dumps())
    root = session.get_node()

    # Assert
    assert root.toplevel.hello == "put something here"  # this is the default


def test_merging_deleting_data_and_setting_it_again():
    log = Mock()
    changes = [
        DataTreeChange(DataTreeChange.ACTION_SET, "/testforms:toplevel/hello", "world"),
        DataTreeChange(DataTreeChange.ACTION_DELETE, "/testforms:toplevel/hello", ""),
        DataTreeChange(DataTreeChange.ACTION_SET, "/testforms:toplevel/hello", "world"),
    ]

    # Act
    session, json_dict, changes = DataTree.process_data_tree_against_libyang(
        {"testforms:topdrop": "b"}, changes, yang_location="yang", log=log
    )
    session2 = yangvoodoo.DataAccess()
    session2.connect("testforms", "yang")
    session2.loads(session.dumps())
    root = session.get_node()

    # Assert
    assert root.toplevel.hello == "world"


def test_creating_and_deleting_list_items():
    log = Mock()
    changes = [
        DataTreeChange(DataTreeChange.ACTION_CREATE_LIST, "/testforms:mainlist", [("mainkey", "a"), ("subkey", "b")]),
        DataTreeChange(DataTreeChange.ACTION_CREATE_LIST, "/testforms:mainlist", [("mainkey", "a"), ("subkey", "b")]),
        DataTreeChange(DataTreeChange.ACTION_CREATE_LIST, "/testforms:mainlist", [("mainkey", "y"), ("subkey", "z")]),
        DataTreeChange(DataTreeChange.ACTION_DELETE_LIST, "/testforms:mainlist[mainkey='x'][subkey='x']", ""),
        DataTreeChange(DataTreeChange.ACTION_CREATE_LIST, "/testforms:mainlist", [("mainkey", "x"), ("subkey", "x")]),
        DataTreeChange(DataTreeChange.ACTION_CREATE_LIST, "/testforms:mainlist", [("mainkey", "z"), ("subkey", "z")]),
        DataTreeChange(DataTreeChange.ACTION_DELETE_LIST, "/testforms:mainlist[mainkey='z'][subkey='z']", ""),
    ]

    # Act
    session, json_dict, changes = DataTree.process_data_tree_against_libyang(
        {"testforms:topdrop": "b"}, changes, yang_location="yang", log=log
    )
    session2 = yangvoodoo.DataAccess()
    session2.connect("testforms", "yang")
    session2.loads(session.dumps())
    root = session.get_node()

    # Assert
    assert len(root.mainlist) == 3
    assert root.mainlist.get_index(0).mainkey == "a"
    assert root.mainlist.get_index(0).subkey == "b"
    assert root.mainlist.get_index(1).mainkey == "y"
    assert root.mainlist.get_index(1).subkey == "z"
    assert root.mainlist.get_index(2).mainkey == "x"
    assert root.mainlist.get_index(2).subkey == "x"
