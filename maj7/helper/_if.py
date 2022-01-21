# from src.helper.Token import Token
from maj7.utils import Token


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
