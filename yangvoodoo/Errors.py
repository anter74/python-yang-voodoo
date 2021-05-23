import libyang


class InvalidValueError(libyang.util.InvalidSchemaOrValueError):
    def __init__(self, value, xpath, error):
        raise libyang.util.LibyangError(
            (
                "The value could not be set, either the value or path is invalid\n"
                f'Value: "{value}"\n'
                f"XPATH: {xpath}\n"
                f"Constraint: {error}\n"
            )
        )


class InvalidListKeyValueError(Exception):
    def __init__(self, v):

        super().__init__("The value of the list key cannot contain both single and double quotes\n%s" % (v))


class NodeHasNoValue(Exception):

    """
    Raised when accessing a non-presence container, list, or anything which does not
    have a value.
    A decendent node is could be fetched.
    """

    def __init__(self, nodetype, xpath):
        super().__init__("The node: %s at %s has no value" % (nodetype, xpath))


class LeafListDoesNotContainIndexError(Exception):
    def __init__(self, len, index, xpath):
        super().__init__(
            "The leaf-list only contains %s elements, could not return index %s\n%s"
            % (len, index, xpath)
        )


class ListDoesNotContainIndexError(Exception):
    def __init__(self, len, index, xpath):
        super().__init__(
            "The list only contains %s elements, could not return index %s\n%s"
            % (len, index, xpath)
        )


class ListDoesNotContainElement(Exception):
    def __init__(self, xpath):
        super().__init__("The list does not contain the list element: %s" % (xpath))


class ListItemCannotBeBlank(Exception):
    def __init__(self, xpath):
        super().__init__("The list item for %s cannot be blank" % (xpath))


class ListKeyCannotBeChanged(Exception):
    def __init__(self, xpath, key):
        super().__init__("The list key: %s for %s cannot be changed" % (key, xpath))


class CannotAssignValueToContainingNode(Exception):
    def __init__(self, xpath):
        super().__init__("Cannot assign a value to %s" % (xpath))


class ListItemsMustBeAccesssedByAnElementError(Exception):
    def __init__(self, xpath, attr):
        msg = (
            "The path: %s is a list access elements like %s by iterating the list or using .get()\n"
            % (xpath, attr)
        )
        super().__init__(msg)


class ListWrongNumberOfKeys(Exception):
    def __init__(self, xpath, require, given):
        super().__init__(
            "The path: %s is a list requiring %s keys but was given %s keys"
            % (xpath, require, given)
        )


class NonExistingNode(Exception):
    def __init__(self, xpath, modules_tested=None):
        if modules_tested:
            super().__init__(
                (
                    f"The path does not point to a valid schema node in the yang module\n\nXPATH: {xpath}\n"
                    f"Searched the following modules\n  - {modules_tested}"
                )
            )
        else:
            super().__init__(
                "The path: %s does not point of a valid schema node in the yang module"
                % (xpath)
            )


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
        super().__init__(
            "There is no subscriber connected able to process data for the following path.\n %s"
            % (xpath)
        )


class BackendDatastoreError(Exception):

    """
    A catch all for errors on the data backend, the exception takes in a list of tuples.
        [ (error-string, xpath) ]
    """

    def __init__(self, errors):
        if len(errors) > 10:
            message = f"{len(errors)} Errors occurred - restricting to the first 10\n"
            cnt = 10
        else:
            message = f"{len(errors)} Errors occured\n"
            cnt = len(errors)

        for c in range(cnt):
            message += f"Error {c}: {errors[c][0]} (Path: {errors[c][1]})\n"

        super().__init__(message)


class XpathDecodingError(Exception):
    def __init__(self, path):
        message = "Unable to decode the following XPATH: %s" % (path)

        super().__init__(message)


class ValueDoesMatchEnumeration(Exception):
    def __init__(self, path, val):
        message = "The value %s is not valid for the enumeration at path %s" % (
            val,
            path,
        )

        super().__init__(message)


class ValueNotMappedToType(Exception):
    def __init__(self, path, val):
        message = (
            "Unable to match the value '%s' to a yang type for path %s - check the yang schema"
            % (val, str(path))
        )

        super().__init__(message)


class ValueNotMappedToTypeUnion(Exception):
    def __init__(self, path, val):
        message = (
            "Unable to match the value '%s' to a yang type for path %s - check the yang schema"
            % (val, str(path))
        )
        message += "\nThis is within a union so may be a type above yangvoodoo's supported complexity threshold"

        super().__init__(message)


class PathIsNotALeaf(Exception):
    def __init__(self, path):
        message = "The path %s is not a leaf." % (path)

        super().__init__(message)


class NodeProvidedIsNotAContainer(Exception):
    def __init__(self):
        message = "Require a containing node not a leaf"

        super().__init__(message)


class ReadonlyError(Exception):
    def __init__(self):

        message = "This node is read-only"

        super().__init__(message)


class NodeAlreadyProvidedCannotChangeSchemaError(Exception):
    def __init__(self):
        message = "A node has already been returned, it is not longer possible to change the schema."

        super().__init__(message)
