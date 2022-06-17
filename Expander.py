import json
import libyang


class SchemaDataExpander:

    YANG_LOCATION = "yang"

    SCHEMA_NODE_TYPE_MAP = {1: "_handle_schema_containing_node", 4: "_handle_schema_leaf", 16: "_handle_schema_list"}
    DATA_NODE_TYPE_MAP = {1: "_handle_data_containing_node", 4: "_handle_data_leaf"}
    LEAF_TYPE_MAP = {10: "string", 6: "enum", 3: "boolean", 5: "empty", 13: "uint8"}

    def __init__(self, yang_module, log):
        self.log = log
        self.ctx = libyang.Context(self.YANG_LOCATION)
        self.ctx.load_module(yang_module)
        self.data_ctx = libyang.DataTree(self.ctx)
        self.yang_module = yang_module

    def process_schema(self):
        """
        Return every node from the schema
        """
        self.log.info("%s processing schema - %s", __name__, self.yang_module)
        self.log.debug("libyang context %s", self.ctx)

        result = {}
        for node in self.ctx.find_path(f"/{self.yang_module}:*"):
            if node.nodetype() not in self.SCHEMA_NODE_TYPE_MAP:
                raise NotImplementedError(f"{node.schema_path()} has unknown type {node.nodetype()}")
            for schema_node in getattr(self, self.SCHEMA_NODE_TYPE_MAP[node.nodetype()])(node):
                result[schema_node["schema"]] = schema_node

        return result

    def _handle_schema_containing_node(self, node):
        yield SchemaDataExpander._form_structure(node, "container")
        for node in self.ctx.find_path(f"{node.schema_path()}/*"):
            if node.nodetype() not in self.SCHEMA_NODE_TYPE_MAP:
                raise NotImplementedError(f"{node.schema_path()} has unknown type {node.nodetype()}")
            yield from getattr(self, self.SCHEMA_NODE_TYPE_MAP[node.nodetype()])(node)

    def _handle_schema_leaf(self, node):
        yield SchemaDataExpander._add_leaf_type(node, SchemaDataExpander._form_structure(node, "leaf"))

    def _handle_schema_list(self, node):
        yield SchemaDataExpander._add_list_key_definition(
            node, SchemaDataExpander._form_structure(node, "list-element")
        )

        for node in self.ctx.find_path(f"{node.schema_path()}/*"):
            if node.nodetype() not in self.SCHEMA_NODE_TYPE_MAP:
                raise NotImplementedError(f"{node.schema_path()} has unknown type {node.nodetype()}")
            yield from getattr(self, self.SCHEMA_NODE_TYPE_MAP[node.nodetype()])(node)

    @staticmethod
    def _form_structure(node, nodetype):
        return {"schema": node.schema_path(), "type": nodetype, "data": {}, "validations": []}

    @classmethod
    def _add_leaf_type(cls, node, structure):
        leaftype = node.type().base()
        if leaftype not in cls.LEAF_TYPE_MAP:
            raise NotImplementedError(f"{node.schema_path()} has unknown leaf type {leaftype}")
        leaftype = cls.LEAF_TYPE_MAP[node.type().base()]
        structure["subtype"] = leaftype

        if leaftype == "enum":
            structure["validations"].append({"explicit": [enum[0] for enum in node.type().enums()]})

        if leaftype == "string":
            patterns = [pattern[0] for pattern in node.type().all_patterns()]
            if patterns:
                structure["validations"].append({"regex": patterns})

        if node.default():
            structure["default"] = node.default()
        else:
            structure["default"] = None
        return structure

    @staticmethod
    def _add_list_key_definition(node, structure):
        structure["keys"] = [key.name() for key in node.keys()]
        return structure

    @staticmethod
    def _get_parent(node):
        if node:
            return node.parent().schema_node()

    @staticmethod
    def _find_best_parent(node):
        try:
            parent = node.parent()
        except libyang.util.LibyangError as err:
            if "cannot use parent() to go above a root node" not in str(err):
                raise
            return ""
        return parent.xpath

    def _handle_data_containing_node(self, schema: dict, schema_node, node):
        schema[schema_node.schema_path()]["data"][node.xpath] = {
            "value": node.value,
            "parent": SchemaDataExpander._find_best_parent(node),
        }

    def _handle_data_leaf(self, schema: dict, schema_node, node):
        schema[schema_node.schema_path()]["data"][node.xpath] = {
            "value": node.value,
            "parent": SchemaDataExpander._find_best_parent(node),
        }

    def process_data(self, schema: dict, data_xml: str):
        """
        Return just schema nodes exapnded out?
        and the post-process data into it?
        """

        self.log.info("Loading data: %s", data_xml)
        self.data_ctx.loads(data_xml)

        for node in self.data_ctx.dump_datanodes():
            if not node.xpath or node.value is None:
                continue
            self.log.debug("%s = '%s'", node.xpath, node.value)
            schema_node = node.get_schema()

            if schema_node.nodetype() not in self.DATA_NODE_TYPE_MAP:
                raise NotImplementedError(
                    f"{schema_node.schema_path()} has unknown type {schema_node.nodetype()} in data processing"
                )
            getattr(self, self.DATA_NODE_TYPE_MAP[schema_node.nodetype()])(schema, schema_node, node)

            print(node)
        return schema
