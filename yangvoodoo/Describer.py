import hashlib
import json
import logging
import sys
import time
from yangvoodoo.SchemaData import Expander


class Yang2Text(Expander):

    FORMATS = {"xml": 1, "json": 2}

    class Options:
        def __init__(self):
            self.schema_xpath = False
            self.data_xpath = False
            self.term_width = 480
            self.min_block_width = 80
            self.limit_revisions = 4
            self.hide_title = False
            self.hide_descriptions = False
            self.hide_types = False
            self.legacy_pyang = False
            self.hide_constraints = False
            self.enable_filter_list = False

    class DullDisplay:
        DIM = ""
        NORMAL = ""
        NORMAL_ = ""
        BRIGHT = ""
        MISSING = ""
        LEAF = "l> "
        CONTAINER = "C> "
        LIST = "L+ "
        LEAF_LIST = "l+ "
        LIST_ELEMENT = "-> "
        MANDATORY = "*"
        WHEN = "! "
        MUST = "% "
        CHOICE = "? "
        CASE = "^ "
        CONSTRAINT = ""
        LINE = "-"
        NEWLINE = "\n"

        TITLE_START = ""
        TITLE_END = ""

        @classmethod
        def get_separator(cls, line):
            return cls.LINE * len(line)

        @staticmethod
        def get_active(active):
            if active:
                return "* "
            return ""

        @staticmethod
        def get_presence(presence):
            if presence:
                return "+ "
            return ""

    class Display(DullDisplay):
        DIM = "\033[2m"
        NORMAL = "\033[22m"
        NORMAL_ = "\033[22m"
        BRIGHT = "\033[1m"
        MISSING = " "
        LEAF = "🍁 "
        CONTAINER = "➜ "
        LIST = "➜ "
        LIST_ELEMENT = "➜ "
        LEAF_LIST = "🍁 "
        MANDATORY = "⚠ "
        WHEN = "☣ "
        MUST = "☢ "
        CHOICE = "➜ "
        CASE = "➜ "
        CONSTRAINT = "🔍 "
        LINE = "-"

        @staticmethod
        def get_active(active):
            if active:
                return "✔ "
            return ""

        @staticmethod
        def get_presence(presence):
            if presence:
                return "✔ "
            return ""

    INCLUDE_BLANK_LIST_ELEMENTS = True
    INDENT_CHAR = "-"
    INDENT_MINIMUM = 1
    INDENT_SPACING = 1

    def __init__(self, yang_module, log):
        super().__init__(yang_module, log)
        self.display = Yang2Text.Display

    def callback_write_title(self, module):
        if self.options.hide_title:
            return
        self.result.write(f"{self.display.TITLE_START}{self.yang_module}{self.display.TITLE_END}{self.display.NEWLINE}")
        self.result.write(f"{self.display.get_separator(self.yang_module)}{self.display.NEWLINE}{self.display.NEWLINE}")
        width = self.options.term_width
        if width < self.options.min_block_width:
            width = self.options.min_block_width
        for word in self.block_quotify(module.description(), width, ""):
            self.result.write(f"{word}")
        self.result.write(f"{self.display.NEWLINE}")
        self.result.write(f"{self.display.NEWLINE}")
        self.result.write(f"Checksum: {hashlib.sha1(str(module).encode('utf-8')).hexdigest()} ")
        self.result.write(f"Generated: {time.ctime()}{self.display.NEWLINE}")
        self.result.write(f"{self.display.NEWLINE}")
        self.result.write(f"{self.display.NEWLINE}")
        revisions = list(module.revisions())
        for rev in revisions[0 : self.options.limit_revisions]:
            width = self.options.term_width - 12
            if width < self.options.min_block_width:
                width = self.options.min_block_width
            self.result.write(f"{rev.date():12}")
            for word in self.block_quotify(rev.description(), width, " " * 12):
                self.result.write(f"{word}")
            self.result.write(f"{self.display.NEWLINE}")
        self.result.write(f"{self.display.NEWLINE}")
        self.result.write(f"{self.display.NEWLINE}")
        if self.options.legacy_pyang:
            print(str(module))
            sys.exit(0)

    def _show_when(self, node):
        if node.when_condition() and not self.options.hide_constraints:
            self.result.write(self.display.NORMAL)
            for line in node.when_condition().split("\n"):
                when = self.display.MUST
                self.result.write(f"{self.get_blank_indent()}      {when}{line}{self.display.NEWLINE}")
                when = ""
            self.result.write(f"{self.display.NEWLINE}")
            self.result.write(self.display.NORMAL)

    def _show_must(self, node):
        if self.options.hide_constraints:
            return
        for cond in node.must_conditions():
            self.result.write(self.display.NORMAL)
            for line in cond.split(f"{self.display.NEWLINE}"):
                must = self.display.WHEN
                self.result.write(f"{self.get_blank_indent()}      {must}{line}{self.display.NEWLINE}")
                must = ""
            self.result.write(self.display.NORMAL)

    def _show_description(self, description):
        if description() and not self.options.hide_descriptions:
            blank_indent = self.get_blank_indent()
            width = self.options.term_width - len(blank_indent)
            if width < self.options.min_block_width:
                width = self.options.min_block_width
            self.result.write(f"{self.display.NEWLINE}{blank_indent}{self.display.DIM}      ")
            for word in self.block_quotify(
                description(),
                width,
                indent=f"{self.display.DIM}{self.get_blank_indent(6)}",
            ):
                word = word.replace("\n", self.display.NEWLINE)
                self.result.write(f"{word}")
            self.result.write(f"{self.display.NEWLINE}")
            self.result.write(f"{self.display.NEWLINE}")
            self.result.write(self.display.NORMAL)

    def _show_types(self, node):
        types = []
        for type, constraints in self.get_human_types(node):
            if constraints:
                types.append(f"{type} {{{':'.join(constraints)}}} ")
            else:
                types.append(type)

        type_string = ", ".join(types)
        if len(type_string) > self.options.term_width - len(self.get_blank_indent()):
            self.result.write(f"{self.display.NEWLINE}")
            for type in types:
                self.result.write(f"{self.get_blank_indent(4)}{self.display.DIM}type: ")
                for word in self.block_quotify(
                    type,
                    self.options.term_width,
                    f"{self.display.DIM}{self.get_blank_indent(10)}",
                ):
                    self.result.write(f"{word}")
                self.result.write(f"{self.display.NEWLINE}")

        else:
            self.result.write(f"{self.display.NEWLINE}{self.get_blank_indent(4)}{self.display.DIM}type:")
            self.result.write(f"{type_string}{self.display.NORMAL}{self.display.NEWLINE}")

    def callback_open_list(self, node, count, node_id):
        self.result.write(
            f"{self.open_indent()}{self.display.LIST} {node.name()} {self.display.DIM} ({count} Item{self.pluralise(count)}) {self.display.NORMAL}{self.display.NEWLINE}"
        )
        self._show_description(node.description)

    def callback_open_list_element(self, node, key_values, empty_list_element, force_open, node_id):
        if empty_list_element:
            self.result.write(
                f"{self.open_indent()} {self.display.NORMAL}{self.display.LIST_ELEMENT}{self.display.DIM}keys: {','.join([k[0] for k in key_values])}{self.display.NORMAL}{self.display.NEWLINE}"
            )
        else:
            self.result.write(f"{self.open_indent()} {self.display.NORMAL}{self.display.LIST_ELEMENT}")
            comma = ""
            for key, value in key_values:
                self.result.write(f"{self.display.DIM}{comma}{key}={self.display.NORMAL}{value}")
                comma = ", "
            self.result.write(f"{self.display.NEWLINE}")

    def callback_close_list_element(self, node):
        self.close_indent()

    def callback_close_list(self, node):
        self.close_indent()

    def _show_paths(self, schema_path, data_path):
        if self.options.data_xpath:
            self.result.write(
                f"{self.get_blank_indent(6)}{self.display.DIM}D: {data_path}{self.display.NORMAL}{self.display.NEWLINE}"
            )
        if self.options.schema_xpath:
            self.result.write(
                f"{self.get_blank_indent(6)}{self.display.DIM}S: {schema_path}{self.display.NORMAL}{self.display.NEWLINE}"
            )

    def callback_write_leaf(self, node, value, quote, explicit, default, key, template, node_id):
        self.result.write(f"{self.get_indent()} {self.display.NORMAL}{self.display.LEAF}")
        if node.mandatory():
            self.result.write(f"{self.display.MANDATORY} ")
        if default and value and value == default:
            self.result.write(f"{node.name()} = {self.display.DIM}{value}{self.display.NORMAL}")
        elif value:
            self.result.write(f"{node.name()} = {value}")
        else:
            self.result.write(f"{node.name()} {self.display.DIM} {self.display.MISSING} {self.display.NORMAL}")
        if not self.options.hide_types:
            self._show_types(node)
        self._show_paths(node.schema_path(), "".join(self.data_path_trail))
        self._show_when(node)
        self._show_description(node.description)

    def callback_open_containing_node(self, node, presence, node_id):
        self.result.write(f"{self.open_indent()} {self.display.NORMAL}{self.display.CONTAINER} ")
        if presence is not None:
            self.result.write(f"{node.name()} {self.display.get_presence(presence)}{self.display.NEWLINE}")
        else:
            self.result.write(f"{node.name()}{self.display.NEWLINE}")

        self._show_must(node)
        self._show_when(node)
        self._show_description(node.description)

    def callback_close_containing_node(self, node):
        self.close_indent()

    def callback_open_leaflist(self, node, count, node_id):
        self.result.write(f"{self.open_indent()} {self.display.NORMAL}{self.display.LEAF_LIST} {node.name()} - ")
        self.result.write(f"- {self.display.DIM}({count} item{self.pluralise(count)}){self.display.NORMAL}")
        if not self.options.hide_types:
            self._show_types(node)
        self._show_description(node.description)
        self.open_indent()
        self.leaf_list_count = 0

    def callback_write_leaflist_item(self, node, quote, explicit, value, template, node_id):
        self.result.write(
            f"{self.get_blank_indent(6)}{self.display.DIM}index {self.leaf_list_count}:{self.display.NORMAL} {value}{self.display.NEWLINE}"
        )
        self.leaf_list_count += 1

    def callback_close_leaflist(self, node):
        self.close_indent()
        self.close_indent()

    def callback_open_choice(self, node, node_id):
        self.result.write(
            f"{self.open_indent()} {self.display.NORMAL}{self.display.CHOICE} {node.name()}{self.display.NEWLINE}"
        )

    def callback_close_choice(self, node):
        self.close_indent()

    def callback_open_case(self, node, active_case, no_active_case, node_id):
        if not active_case:
            self.result.write(self.display.DIM)
            self.display.NORMAL = self.display.DIM
        self.result.write(
            f"{self.get_indent()}{self.display.CASE} {self.display.get_active(active_case)} {node.name()}{self.display.NEWLINE}"
        )
        self.open_indent()

    def callback_close_case(self, node):
        self.close_indent()
        self.display.NORMAL = self.display.NORMAL_
        self.result.write(self.display.NORMAL)


class Yang2HTML(Yang2Text):
    class Display(Yang2Text.DullDisplay):
        DIM = ""
        NORMAL = ""
        NORMAL_ = ""
        BRIGHT = ""

    """
    We could override callback methods to wrap their output with super() inside
    of div's, apply more styling to make a HTML version of this page
    """
