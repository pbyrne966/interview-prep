from enum import Enum
from dataclasses import dataclass
from typing import Optional, Iterable, Callable


class Delimeters(Enum):
    OPENING = "("
    CLOSING = ")"
    SEQ = ";"
    OPENING_NODE = "["
    CLOSING_NODE = "]"


RAW_DELIMS = set([d.value for d in Delimeters._member_map_.values()])


@dataclass
class StateManagement:
    in_bracket: bool = False
    found_seq: bool = False
    append_node: bool = False

    def __repr__(self):
        return f"in_bracket={self.in_bracket}, found_seq={self.found_seq}, append_node={self.append_node}"


class SgfTree:
    def __init__(self, properties=None, children=None):
        self.properties = properties or {}
        self.children = children or []

    def __eq__(self, other):
        if not isinstance(other, SgfTree):
            return False
        for key, value in self.properties.items():
            if key not in other.properties:
                return False
            if other.properties[key] != value:
                return False
        for key in other.properties.keys():
            if key not in self.properties:
                return False
        if len(self.children) != len(other.children):
            return False
        for child, other_child in zip(self.children, other.children):
            if child != other_child:
                return False
        return True

    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        if self.children:
            return f"Properties={self.properties}, Children={self.children}"
        else:
            return f"Properties={self.properties}"


def validate_input(nodes: str):
    if nodes in ["()"]:
        raise ValueError("tree with no nodes")
    if nodes in ["", ";"]:
        raise ValueError("tree missing")


def handle_non_delimiter(
    c: str,
    state: StateManagement,
    curr_root: Optional[SgfTree],
    root_key: str,
    built_char: str,
    raw_chars: Iterable,
) -> tuple[Optional[SgfTree], str, str]:
    if state.in_bracket and state.found_seq and not root_key:
        if curr_root is None:
            curr_root = SgfTree({root_key: []})
        else:
            curr_root.properties[root_key] = []
    elif state.append_node and curr_root is not None:
        built_char += c
    elif root_key != c:
        root_key = consume_til_predicate(raw_chars, c, state)
        curr_root.properties[root_key] = []
    return curr_root, root_key, built_char


def consume_til_predicate(
    chars: Iterable,
    c: str,
    state: StateManagement,
    predicate: Callable[[str], bool] = lambda x: x not in ["[", "]"],
    consume_all: bool = False,
) -> str:

    joined = c if (consume_all or c not in RAW_DELIMS) else ""

    current = c

    while predicate(current):
        try:
            current = next(chars)
            if current == "\\":
                continue
            if consume_all or current not in RAW_DELIMS:
                joined += current
        except:
            break

    state.found_seq = True
    state.append_node = True

    return joined


def parse(input_string: str) -> Optional[SgfTree]:
    validate_input(input_string)
    if input_string == "(;)":
        return SgfTree()

    raw_chars = iter(input_string)
    state = StateManagement()
    curr_root: Optional[SgfTree] = None
    built_char = ""
    root_key = ""

    for c in raw_chars:
        flag = state.append_node
        print("Line",root_key, c, curr_root, state, flag)
        
        if c not in RAW_DELIMS:
            curr_root, root_key, built_char = handle_non_delimiter(
                c, state, curr_root, root_key, built_char, raw_chars
            )

        if c == Delimeters.OPENING.value:
            if flag:
                print("DEBUG: OPENING delimiter block reached with append_node=True")
            state.in_bracket = True

        elif c == Delimeters.SEQ.value and not state.append_node:
            if flag:
                print("DEBUG: SEQ delimiter block reached with append_node=True")
            if not state.found_seq:
                root_key = consume_til_predicate(raw_chars, c, state)
                if curr_root is None:
                    curr_root = SgfTree({root_key: []})
            else:
                cut_chars = consume_til_predicate(
                    raw_chars, c, state, lambda x: x not in [")"], consume_all=True
                )
                child = parse(cut_chars)
                curr_root.children.append(child)
        elif c == Delimeters.CLOSING.value:
            if flag:
                print("DEBUG: CLOSING delimiter block reached with append_node=True")
            state.in_bracket = False
        elif c == Delimeters.OPENING_NODE.value:
            if flag:
                print("DEBUG: OPENING_NODE delimiter block reached with append_node=True")
            if not state.append_node:
                state.append_node = True
            else:
                cut_chars = consume_til_predicate(
                    raw_chars, c, state, lambda x: x not in ["]"], consume_all=True
                )
                built_char += cut_chars
        elif c == Delimeters.CLOSING_NODE.value:
            if flag:
                print("DEBUG: CLOSING_NODE delimiter block reached with append_node=True")
            state.append_node = False
            curr_root.properties[root_key].append(built_char)
            built_char = ""

    # if not all((p.isupper() for p in curr_root.properties.keys())):
    #     raise ValueError("property must be in uppercase")

    return curr_root


if __name__ == "__main__":
    # expected = SgfTree(
    #     properties={"A": ["a;b", "foo"], "B": ["bar"]},
    #     children=[SgfTree({"C": ["baz"]})],
    # )
    # print(parse("(;A[a;b][foo]B[bar];C[baz])") == expected)

    # input_string = "(;A[x[y\\]z][foo]B[bar];C[baz])"
    # expected = SgfTree(
    #     properties={"A": ["x[y]z", "foo"], "B": ["bar"]},
    #     children=[SgfTree({"C": ["baz"]})],
    # )
    # print(parse(input_string) == expected)

    # input_string = "(;A[hello\\\tworld])"
    # expected = SgfTree(properties={"A": ["hello world"]})
    # print(parse(input_string), expected)

    # input_string = "(;A[hello\\\nworld])"
    # expected = SgfTree(properties={"A": ["helloworld"]})
    # print(parse(input_string), expected)

    # input_string = "(;A[\\t = t and \\n = n])"
    # expected = SgfTree(properties={"A": ["t = t and n = n"]})
    # print(parse(input_string), expected)

    # input_string = "(;A[\\]b\nc\\\nd\t\te\\\\ \\\n\\]])"
    # expected = SgfTree(properties={"A": ["]b\ncd  e\\ ]"]})
    # print(parse(input_string), expected)

    input_string = "(;A[B](;B[C])(;C[D]))"
    expected = SgfTree(
        properties={"A": ["B"]},
        children=[SgfTree({"B": ["C"]}), SgfTree({"C": ["D"]})],
    )
    print(parse(input_string))
    print(expected)
