from maj7.utils import Token


class Section:

    def __init__(self, name: str, instructions: list[Token], type: str):
        self.name = name
        self.instructions = instructions
        self.type = type

    def __str__(self):
        return f"Section({self.type}, {self.name}, {self.instructions})"

    def __repr__(self):
        return f"Section({self.type}, {self.name}, {self.instructions})"