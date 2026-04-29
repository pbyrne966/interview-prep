from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(eq=True)
class SgfTree:
    properties: dict[str, list[str]] = field(default_factory=dict)
    children: list["SgfTree"] = field(default_factory=list)


class SgfParser:
    def __init__(self, text: str):
        self.text = text
        self.i = 0

    def parse(self) -> SgfTree:
        if not self.text:
            raise ValueError("tree missing")

        tree = self._parse_tree()

        if self.i != len(self.text):
            raise ValueError("unexpected data after tree")

        return tree

    def _parse_tree(self) -> SgfTree:
        self._expect("(")

        if self._peek() == ")":
            raise ValueError("tree with no nodes")

        root = self._parse_sequence()

        self._expect(")")
        return root

    def _parse_sequence(self) -> SgfTree:
        self._expect(";")

        node = self._parse_node()

        while self._peek() == ";":
            self._expect(";")
            node.children.append(self._parse_node())

        while self._peek() == "(":
            node.children.append(self._parse_tree())

        return node

    def _parse_node(self) -> SgfTree:
        properties: dict[str, list[str]] = {}

        while self._peek() and self._peek().isalpha():
            key = self._parse_property_key()
            values = self._parse_property_values()

            if not values:
                raise ValueError("properties without delimiter")

            properties.setdefault(key, []).extend(values)

        return SgfTree(properties)

    def _parse_property_key(self) -> str:
        start = self.i

        while self._peek() and self._peek().isalpha():
            self.i += 1

        return self.text[start : self.i]

    def _parse_property_values(self) -> list[str]:
        values = []

        while self._peek() == "[":
            values.append(self._parse_property_value())

        return values

    def _parse_property_value(self) -> str:
        self._expect("[")
        chars: list[str] = []

        while True:
            c = self._next()

            if c is None:
                raise ValueError("unterminated property value")

            if c == "]":
                break

            if c == "\\":
                escaped = self._next()

                if escaped is None:
                    break

                if escaped in "\n\r":
                    continue

                if escaped == "\t":
                    chars.append(" ")
                else:
                    chars.append(escaped)

            elif c == "\t":
                chars.append(" ")
            else:
                chars.append(c)

        return "".join(chars)

    def _peek(self) -> str | None:
        if self.i >= len(self.text):
            return None
        return self.text[self.i]

    def _next(self) -> str | None:
        if self.i >= len(self.text):
            return None

        c = self.text[self.i]
        self.i += 1
        return c

    def _expect(self, expected: str) -> None:
        actual = self._next()

        if actual != expected:
            raise ValueError(f"expected {expected!r}, got {actual!r}")


def deep_recur(sgf_tree: SgfTree):
    top_level = all((elem.isupper() for elem in sgf_tree.properties.keys()))
    if not top_level:
        raise ValueError("property must be in uppercase")

    for child in sgf_tree.children:
        deep_recur(child)


def parse(input_string: str) -> SgfTree:
    if input_string in {"", ";"}:
        raise ValueError("tree missing")

    tree = SgfParser(input_string).parse()
    deep_recur(tree)

    return tree


if __name__ == "__main__":
    input_string = "(;A)"
    output = parse(input_string)
    print(output)
