from maj7.utils import Token


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

