import base64
import json
import logging
from typing import Generator, List, Tuple
import libyang
from yangvoodoo import DataAccess


def base64_tostring(input_string):
    return base64.b64decode(input_string.encode("utf-8")).decode("utf-8")


class DataTreeChange:

    ACTION_SET = "set"
    ACTION_DELETE = "delete"

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
        DataTreeChange.ACTION_DELETE,
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
        json_dict: dict, changes: List[DataTreeChange], yang_location: str = None, log=logging.Logger
    ) -> Tuple[DataAccess, dict, List[DataTreeChange]]:
        """
        Load a yang model from a given payload Merge the changes to the base data tree. In this case if we are asked
        to merge in an action which violates the YANG model the exception will not be instantly raised but instead
        the XPATH is marked a failed. If a later change for that XPATH subsequently sets valid data the failure is
        forgotten about. If the the failure has not been corrected the first such instance will be raised.


        Args:
            json_dict: A dcitionary matching the JSON encoded data for a YANG model.
            changes: A list of changes
            yang_location: A location to look for yang modles
            log: A python logger
        """

        session = DataTree.connect_yang_model(json_dict, yang_location)
        log.info("Loading initial JSON payload for %s...", session.module)
        session.loads(json.dumps(json_dict), 2)

        failed_xpaths = {}

        for change in changes:
            if change.action in (DataTreeChange.ACTION_SET, DataTreeChange.ACTION_DELETE):
                try:
                    if change.action == DataTreeChange.ACTION_SET:
                        session.set(change.xpath, change.value)
                    elif change.action == DataTreeChange.ACTION_DELETE:
                        session.uncreate(change.xpath)
                    log.info("%s", change)
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

        log.info("Final Data tree: %s", session.dumps(2))
        return session, json.loads(session.dumps(2)), []
