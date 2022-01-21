
class For:
    def __init__(self, n, instructions):
        self.n = n
        self.instructions = instructions

    def __str__(self):
        return f"For({self.n}, {self.instructions}"

    def __repr__(self):
        return f"For({self.n}, {self.instructions}"
