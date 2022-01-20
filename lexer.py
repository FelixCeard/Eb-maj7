import re
from .utils import *


class Lexer:
    def __init__(self, string):
        self.tokens = []
        self.string = re.sub(r"(^[\n ]+)", "", string)

    def lex(self):
        # get every line
        lines = self.string.split('\n')
        for i, line in enumerate(lines):
            group = ""
            t = "string"
            for c in line:
                # check if number is over
                if len(group) > 0 and self.isNumber(c) == False:
                    if t == "number":
                        self.tokens.append(Token("NUMBER", group, line=i))
                        t = "string"
                        group = ""

                if self.isNumber(c):
                    if len(group) > 0:
                        if t == "string":
                            self.tokenize(group, line=i)
                            group = c
                            t = "number"
                        else:
                            group += c
                    else:
                        t = "number"
                        group += c
                elif self.isChar(c):
                    group += c

                elif c == " ":
                    self.tokenize(group, line=i)
                    group = ""
                else:
                    if len(group) > 0:
                        if c == "#":
                            group += c
                        elif c == ",":
                            group += c
                        else:
                            self.tokenize(group, line=i)
                            group = ""
                            self.tokens.append(Token("SPECIAL", c, line=i))
                    else:
                        self.tokens.append(Token("SPECIAL", c, line=i))

            if t == "string":
                self.tokenize(group, line=i)
            else:
                self.tokens.append(Token("NUMBER", group, line=i))

            self.tokenize("\n", line=i)

        self.relex()
        return self.tokens

    def tokenize(self, group: str, line):
        match group:
            case "\n":
                self.tokens.append(Token("NEWLINE", "", line=line))
            case "":
                pass
            case _:
                self.tokens.append(Token("STRING", group, line=line))

    def isChar(self, c):
        number = ord(c)

        if 64 < number < 91:
            return True
        elif 96 < number < 123:
            return True
        else:
            return False

    def isNumber(self, c):
        numbers = ord(c)
        return 47 < numbers < 58

    def remove_nones(self):
        list = []
        last = None
        line = None
        for token in self.tokens:
            if last == None:
                if token != None and token.type != "Comment":
                    list.append(token)
                    last = token
            else:
                if token != None and token.type != "Comment":
                    if token.type != last.type or token.content != last.content:
                        if token.type == "STRING":
                            list.append(Token("STRING", token.content.replace(' ', ''), token.line))
                        else:
                            list.append(token)
                        last = token
                    elif token.type == "SPECIAL" and token.content("#"):
                        list.append(token)
                    elif token.type == "SPECIAL" and token.content == "=":
                        list[-1] = Token("EQUALS", line=list[-1].line)
                    elif token.type == "NEWLINE":
                        pass
                    else:
                        raise LexException(f"Unexpected token on line {token.line}")

        self.tokens = list
        self.concat_strings()

    def relex(self):
        fresh_line = False
        context = "NONE"
        last_in = -1

        for i in range(len(self.tokens)):
            has_next = (i < len(self.tokens) - 1)
            if has_next:
                next_token = self.tokens[i + 1]

            token: Token = self.tokens[i]

            if token is None:
                continue

            if context == "comment":
                if token.type != "NEWLINE":
                    last_in = -1
                    self.tokens[i] = None
                    token = None

            if token is None:
                continue

            if token.type == "NEWLINE":
                fresh_line = True
                context = "NONE"
                last_in = -1
                continue

            if token.type == "STRING":
                match token.content:
                    case "smash":
                        if fresh_line:
                            context = "smash"
                            self.tokens[i] = Token("SMASH", line=self.tokens[i].line / 2)
                        else:
                            raise LexException(
                                f"[ERROR]: expected the keyword \"smash\" on the start of a new line, not on line {token.line}")
                    case "play":
                        if fresh_line:
                            context = "play"
                            self.tokens[i] = Token("PLAY", line=self.tokens[i].line / 2)
                        else:
                            raise LexException(
                                f"[ERROR]: expected the keyword \"play\" on the start of a new line, not on line {token.line}")
                    case "Chord":
                        if fresh_line and context == "NONE":
                            context = "chord"
                            self.tokens[i] = Token("CHORD", line=self.tokens[i].line / 2)
                        else:
                            raise LexException(
                                f"[ERROR]: expected the keyword \"Chord\" on the start of a new line, not on line {token.line}")
                    case "forte":
                        if context in ["NONE", "piano", "play"]:
                            self.tokens[i] = Token("FORTE", line=self.tokens[i].line / 2)
                            context = "forte"
                        else:
                            raise LexException(
                                f"[ERROR]: \"[press|smash] forte <value>\" is the syntax for forte, please stick with it on line {self.tokens[i].line / 2}")
                    case "piano":
                        if context in ["NONE", "forte", "play"]:
                            self.tokens[i] = Token("PIANO", line=self.tokens[i].line / 2)
                        else:
                            raise LexException(
                                f"[ERROR]: please stick with the syntax for \"piano\" it on line {self.tokens[i].line / 2}")

                    case "hamonize" | "hamonizes" | "harmony" | "harmonizes":
                        if context == "NONE":
                            self.tokens[i] = Token("HARMONY", line=self.tokens[i].line / 2)
                        else:
                            raise LexException(
                                f"[ERROR]: unexpected context for the keyword \"harmony\" on line {self.tokens[i].line / 2}")
                    case "Tenuto" | "tenuto":
                        self.tokens[i] = Token("TENUTO", line=self.tokens[i].line / 2)

                    case "hard":
                        if context == "press" or context == "smash":
                            self.tokens[i] = Token("HARD", line=self.tokens[i].line / 2)
                        else:
                            raise LexException(
                                f"[ERROR]: the keywor \"hard\" is only usable after a the keyword press or smash on line {self.tokens[i].line / 2}")

                    case "press":
                        if fresh_line:
                            context = "press"
                            self.tokens[i] = Token("PRESS", line=self.tokens[i].line / 2)
                        else:
                            raise LexException(
                                f"[ERROR]: expected the keyword \"press\" on the start of a new line, not on line {self.tokens[i].line / 2}")

                    case "Bar":
                        if fresh_line:
                            context = "bar"
                            self.tokens[i] = Token("BAR", line=self.tokens[i].line / 2)
                        else:
                            raise LexException(
                                f"[ERROR]: expected the keyword \"Bar\" on the start of a new line, not on line {self.tokens[i].line / 2}")

                    case "in":
                        if context == "NONE":
                            if last_in == -1:
                                self.tokens[i] = Token("IN", line=self.tokens[i].line / 2)
                                last_in = i
                            else:
                                self.tokens[last_in] = Token("STRING", "in", line=self.tokens[i].line / 2)

                    case "Time":
                        if context == "NONE":
                            self.tokens[i] = Token("TIME", line=self.tokens[i].line / 2)
                            # context = "Time" useless
                        else:
                            raise LexException(
                                f"[ERROR]: unexpected keyword \"Time\" on line {self.tokens[i].line / 2}")

                    case "Composed":
                        if context == "NONE":
                            self.tokens[i] = Token("COMPOSED", line=self.tokens[i].line / 2)
                        else:
                            raise LexException(
                                f"[ERROR]: unexpected keyword \"Composed\" on line {self.tokens[i].line / 2}")

                    case "opening":
                        if context == "NONE" or fresh_line:
                            self.tokens[i] = Token("OPENING", line=self.tokens[i].line / 2)
                        else:
                            raise LexException(
                                f"[ERROR]: unexpected keyword \"opening\" on line {self.tokens[i].line / 2}")

                    case "LeftHand":
                        self.tokens[i] = Token("VARIABLE", token.content, line=self.tokens[i].line / 2)
                    case "RightHand":
                        self.tokens[i] = Token("VARIABLE", token.content, line=self.tokens[i].line / 2)
                    case "listen":
                        if context == "declaration":
                            self.tokens[i] = Token("LISTEN", line=self.tokens[i].line / 2)
                        else:
                            raise LexException(
                                f"[ERROR]: the keyword \"listen\" should be used only after \":=\" on line {self.tokens[i].line / 2}")
                    case _:
                        pass

            if token.type == "SPECIAL":
                match token.content:
                    case "#":
                        if context == "NONE":
                            context = "comment"
                            self.tokens[i] = Token("Comment")
                        # no else here, should not be useful

                    case ":":
                        if has_next:
                            if next_token.type == "SPECIAL":
                                if next_token.content == "=":
                                    # :=
                                    self.tokens[i] = Token("DECLARATION")
                                    self.tokens[i + 1] = None
                                    context = "declaration"
                                if next_token.content == "|":
                                    self.tokens[i] = Token("LOOP_END")
                                    self.tokens[i + 1] = None
                    case "|":
                        if has_next:
                            if next_token.type == "SPECIAL":
                                if next_token.content == ":":
                                    self.tokens[i] = Token("LOOP_START")
                                    self.tokens[i + 1] = None
                                    context = "loop"
                    case "/":
                        pass
                    case "(" | ")" | "-":
                        pass
                    case _:
                        pass

        self.remove_nones()

    def concat_strings(self):
        l = []

        was_past_string = False
        string = ""
        first_line = None

        for token in self.tokens:
            if token.type == "STRING":
                if not was_past_string:
                    was_past_string = True
                    first_line = token.line
                string += token.content + " "
            else:
                if was_past_string:
                    l.append(Token("STRING", string, first_line))
                    first_line = None
                    string = ""
                    was_past_string = False
                l.append(token)

        self.tokens = l

        self.group_to_lines()

    def group_to_lines(self):
        lines = []
        line = []

        for token in self.tokens:
            if token.type == "NEWLINE" and len(line) > 0:
                lines.append(line)
                line = []
            else:
                line.append(token)

        self.tokens = lines


if __name__ == '__main__':
    pass
