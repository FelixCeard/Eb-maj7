"""
Helper classes for the interpreter
"""


class Token:
    def __init__(self, type: str, content="", line=-1):
        if content == "":
            content = type.lower()
        self.type = type
        self.content = content
        self.line = line

    def __repr__(self):
        return f"TOKEN: ({self.type}, {self.content}, {self.line})"

    def __str__(self):
        return f"TOKEN: ({self.type}, {self.content}, {self.line})"

    def __len__(self):
        return len(self.content)

    def to_string(self):
        return f"TOKEN: ({self.type}, {self.content})"


class If:
    def __init__(self, left: Token, right: Token, then: Token, or_else: Token | None):
        self.left = left
        self.right = right
        self.then = then
        self.else_ = or_else
        self.has_else = or_else is not None

    def __len__(self):
        return 1

    def __str__(self):
        return f"IF({self.left}, {self.right}, {self.then}, {self.else_})"

    def __repr__(self):
        return f"IF({self.left}, {self.right}, {self.then}, {self.else_})"


class Section:

    def __init__(self, name: str, instructions: list[Token], type: str):
        self.name = name
        self.instructions = instructions
        self.type = type

    def __str__(self):
        return f"Section({self.type}, {self.name}, {self.instructions})"

    def __repr__(self):
        return f"Section({self.type}, {self.name}, {self.instructions})"


class Declaration:
    def __init__(self, left: list[Token], right: Token):
        self.left = left
        self.right = right

    def __str__(self):
        return f"Declaration({self.left} = {self.right})"

    def __repr__(self):
        return f"Declaration({self.left} = {self.right})"

    def __len__(self):
        return len(self.left) + len(self.right)


class For:
    def __init__(self, n, instructions):
        self.n = n
        self.instructions = instructions

    def __str__(self):
        return f"For({self.n}, {self.instructions}"

    def __repr__(self):
        return f"For({self.n}, {self.instructions}"


class ParseException(Exception):
    def __init__(self, string=""):
        super(ParseException, self).__init__(string)


class LexException(Exception):
    def __init__(self, string:str):
        super(LexException, self).__init__()
        print(string)

if __name__ == '__main__':
    pass
