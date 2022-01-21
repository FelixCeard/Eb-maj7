class Token:
    def __init__(self, type:str, content="", line=-1):
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
