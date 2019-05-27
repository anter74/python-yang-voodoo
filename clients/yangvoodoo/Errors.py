
class NodeHasNoValue(Exception):

    """
    Raised when accessing a non-presence container, list, or anything which does not
    have a value.
    A decendent node is could be fetched.
    """

    def __init__(self, nodetype, xpath):
        super().__init__("The node: %s at %s has no value" % (nodetype, xpath))


class NodeNotAList(Exception):

    def __init__(self, xpath):
        super().__init__("The path: %s is not a list" % (xpath))


class ListDoesNotContainElement(Exception):

    def __init__(self, xpath):
        super().__init__("The list does not contain the list element: %s" % (xpath))


class ListItemCannotBeBlank(Exception):

    def __init__(self, xpath):
        super().__init__("The list item for %s cannot be blank" % (xpath))


class ListKeyCannotBeBlank(Exception):

    def __init__(self, xpath, key):
        super().__init__("The list key: %s for %s cannot be blank" % (key, xpath))


class ListKeyCannotBeChanged(Exception):

    def __init__(self, xpath, key):
        super().__init__("The list key: %s for %s cannot be changed" % (key, xpath))


class ListWrongNumberOfKeys(Exception):

    def __init__(self, xpath, require, given):
        super().__init__("The path: %s is a list requiring %s keys but was given %s keys" % (xpath, require, given))


class NonExistingNode(Exception):

    def __init__(self, xpath):
        super().__init__("The path: %s does not point of a valid schema node in the yang module" % (xpath))


class NothingToCommit(Exception):

    def __innit__(self, message):
        super().__init__("No channges to commit")


class CommitFailed(Exception):

    def __init__(self, message):
        super().__init__("The commit failed.\n%s" % (message))


class NotConnect(Exception):

    def __init__(self):
        super().__init__("Not connected to the datastore - try to reconnect.\n")


class SubscriberNotEnabledOnBackendDatastore(Exception):

    def __init__(self, xpath):
        super().__init__("There is no subscriber connected able to process data for the following path.\n %s" % (xpath))


class BackendDatastoreError(Exception):

    """
    A catch all for errors on the data backend, the exception takes in a list of tuples.
        [ (error-string, xpath) ]
    """

    def __init__(self, errors):
        if len(errors) > 10:
            message = "%s Errors occurred - restricting to the first 10\n" % (len(errors))
            cnt = 10
        else:
            message = "%s Errors occured\n" % (len(errors))
            cnt = len(errors)

        for c in range(cnt):
            message = message + "Error %s: %s (Path: %s)\n" % (c, errors[c][0], errors[c][1])

        super().__init__(message)


class XmlTemplateParsingBadKeys(Exception):

    def __init__(self, key_expected, key_found):
        if not key_found:
            key_found = "nothing"
        message = "Expecting to find list key '%s' but found '%s' instead" % (key_expected, key_found)

        super().__init__(message)


class XpathDecodingError(Exception):

    def __init__(self, path):
        message = "Unable to decode the following XPATH: %s" % (path)

        super().__init__(message)
