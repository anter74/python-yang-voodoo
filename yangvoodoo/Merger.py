import base64
import json
import logging
from typing import Generator, List, Tuple
import libyang
from yangvoodoo import DataAccess
from yangvoodoo import Types
from yangvoodoo.Common import Utils


def base64_tostring(input_string):
    return base64.b64decode(input_string.encode("utf-8")).decode("utf-8")


class DataTreeChange:

    ACTION_SET = "set"
    ACTION_SET_EMPTY = "set_empty"
    ACTION_SET_BOOLEAN = "set_boolean"
    ACTION_DELETE = "delete"
    ACTION_CREATE_LIST = "create_list_xpath"
    ACTION_DELETE_LIST = "delete_list_xpath"

    def __init__(self, action: str, xpath: str, value: str, base64_path: bool = False):
        """
        A description of a discrete change to a data tree.

        Args:
            action: `set`
            xpath: An XPATH to set
            value: The value to set (Note: libyang's representation of '' for presence containers, empty leaves)
        """
        self.action = action
        if base64_path:
            self.xpath = base64_tostring(xpath)
        else:
            self.xpath = xpath
        self.value = value

    def __repr__(self):
        return f"{self.action}: {self.xpath} -> {self.value}"


class DataTreeChanges:

    ACTIONS = (
        DataTreeChange.ACTION_SET,
        DataTreeChange.ACTION_SET_EMPTY,
        DataTreeChange.ACTION_SET_BOOLEAN,
        DataTreeChange.ACTION_DELETE,
        DataTreeChange.ACTION_CREATE_LIST,
        DataTreeChange.ACTION_DELETE_LIST,
    )

    @staticmethod
    def convert(input_change_list: List[dict]) -> Generator[DataTreeChange, None, None]:
        """
        Convert a JSON representation of a change (potentially with path's encoded as base64 strings) to
        a DataTreeChange.

        Args:
            input_chage_list: A list of dictionary with action, path/baes64_path, and value keys.

        Yields:
            A corresponding set of DataTreeChange instances.
        """
        for change in input_change_list:
            try:
                if "base64_path" in change:
                    yield DataTreeChange(change["action"], change["base64_path"], change["value"], base64_path=True)
                else:
                    yield DataTreeChange(change["action"], change["path"], change["value"])
            except KeyError as err:
                raise ValueError(f"Cannot create a DataTreeChange from %s\n%s", change, str(err))


class DataTree:

    ADDITIONAL_YANG_MODELS = {}

    @staticmethod
    def get_root_yang_model(json_dict: dict) -> str:
        for key in json_dict:
            return key.split(":")[0]
        raise ValueError("Unable to determine yang model from payload")

    @classmethod
    def connect_yang_model(cls, json_dict: dict, yang_location: str) -> DataAccess:
        """
        From a given JSON object conforming to a yang model determine the name of the yang model
        to load.

        Args:
            json_dict: the data associated with a json instance data
            yang_location: load yang from a given yang directory
        """
        session = DataAccess()
        yang_model = cls.get_root_yang_model(json_dict)
        session.connect(yang_model, yang_location)
        if yang_model in cls.ADDITIONAL_YANG_MODELS:
            for yang_model in cls.ADDITIONAL_YANG_MODELS[yang_model]:
                session.add_module(yang_model)

        return session

    @staticmethod
    def process_data_tree_against_libyang(
        json_dict: dict,
        changes: List[DataTreeChange],
        yang_location: str = None,
        format: str = "json",
        log=logging.Logger,
    ) -> Tuple[DataAccess, dict, List[DataTreeChange]]:
        """
        Load a yang model from a given payload Merge the changes to the base data tree. In this case if we are asked
        to merge in an action which violates the YANG model the exception will not be instantly raised but instead
        the XPATH is marked a failed. If a later change for that XPATH subsequently sets valid data the failure is
        forgotten about. If the the failure has not been corrected the first such instance will be raised.

        Creation/Deletion of List Elements is supressed to the end - this is done so that if a user adds a list element,
        removes it and then adds it again the final add/remove it will happen. This works well if a UI simply hides the
        list element until this processing (submit) step - but this means that if the user adds a list element, sets a
        non-key value/child of that list elements, deletes it and adds it back - it won't be empty but include the
        old contents. The assumption is a UI would allow a user to delete the list element and then 'commit' or 'submit'
        the data. to force a full removal of the children of the list element.

        Args:
            json_dict: A dcitionary matching the JSON encoded data for a YANG model.
            changes: A list of changes
            yang_location: A location to look for yang modles
            fomrat: the libyang format to use (json or xml)
            log: A python logger
        """

        session = DataTree.connect_yang_model(json_dict, yang_location)
        log.info("Loading initial JSON payload for %s...", session.module)
        session.loads(json.dumps(json_dict), Types.FORMAT[format.upper()])

        failed_xpaths = {}
        list_elements = {}

        for change in changes:
            if change.action in DataTreeChanges.ACTIONS:
                try:
                    log.info("processing change: %s", change)
                    if change.action == DataTreeChange.ACTION_SET:
                        session.set(change.xpath, change.value)
                    if change.action == DataTreeChange.ACTION_SET_EMPTY:
                        if change.value == "on":
                            session.set(change.xpath, "")
                        else:
                            session.uncreate(change.xpath)
                    if change.action == DataTreeChange.ACTION_SET_BOOLEAN:
                        if change.value == "on":
                            session.set(change.xpath, "true")
                        else:
                            session.set(change.xpath, "false")
                    elif change.action == DataTreeChange.ACTION_DELETE:
                        session.uncreate(change.xpath)
                    elif change.action == DataTreeChange.ACTION_CREATE_LIST:
                        predicates = ""
                        for k, v in change.value:
                            predicates += Utils.encode_xpath_predicate(k, v)

                        list_elements[f"{change.xpath}{predicates}"] = True
                    elif change.action == DataTreeChange.ACTION_DELETE_LIST:
                        list_elements[f"{change.xpath}"] = False
                    if change.xpath in failed_xpaths:
                        del failed_xpaths[change.xpath]
                except libyang.util.LibyangError as err:
                    failed_xpaths[change.xpath] = err
                    log.error("Ingoring libyang exception %s", change.xpath)
            else:
                raise NotImplementedError(f"Change Type: {change.action} not supported")

        log.info("FAILED PATHS: %s", failed_xpaths)
        for xpath in failed_xpaths:
            raise failed_xpaths[xpath]

        log.info("Create or Uncreate List elements; %s", list_elements)
        for xpath in list_elements:
            if list_elements[xpath] is True:
                session.create(xpath)
            elif list_elements[xpath] is False:
                session.uncreate(xpath)

        log.info("Final Data tree: %s", session.dumps(2))
        return session, json.loads(session.dumps(2)), []
