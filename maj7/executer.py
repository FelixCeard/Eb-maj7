import re

from .utils import *


class Executor:

    def __init__(self, tokens: list[Token]):
        self.BREAK = False
        self.tokens = tokens
        self.title = None
        self.key = None
        self.author = None
        self.year = None
        self.list_name = None
        self.tempo = None
        self.opening = None

        self.things = {}  # saves the name and the type (Bar/Chord)
        self.bars = {}
        self.chords = {}
        self.list = {}  # dict because index => value

        self.get_header()
        self.gen_things_dict()
        self.check_start()

        self.history = []

        self.execute(self.bars.get(self.opening))

        print("\n" + "----" * 6 + "\n" + "Successfully finished")

    def get_header(self):

        for i, token in enumerate(self.tokens):
            if self.title and self.key and self.author and self.year and self.list_name and self.tempo and self.opening:
                self.tokens = self.tokens[i:]
                return

            if token.type == "TITLE":
                self.title = token.content

            elif token.type == "KEY":
                self.key = token.content

            elif token.type == "AUTHOR":
                self.author = token.content

            elif token.type == "YEAR":
                self.year = token.content

            elif token.type == "LIST_NAME":
                self.list_name = token.content

            elif token.type == "TEMPO":
                self.tempo = token.content

            elif token.type == "OPENING":
                self.opening = token.content

            else:
                raise ParseException(f"[ERROR]: expected a header element, got a {token.type}")

        raise ParseException("[ERROR]: missing thing in header")

    def gen_things_dict(self):

        for token in self.tokens:
            if token.type == "BAR":
                self.things[self.format(token.content.name)] = "BAR"
                self.bars[token.content.name] = token.content.instructions
            elif token.type == "CHORD":
                self.things[self.format(token.content.name)] = "CHORD"
                self.chords[token.content.name] = token.content.instructions
            else:
                raise ParseException("[ERROR]: can't have declarations etc... outside a Bar/Chord")

    def check_start(self):
        if self.bars.get(self.opening) == None:
            raise ParseException(f"[ERROR]: can't find opening bar named {self.opening}")

    def execute(self, o, LeftHand=None, RightHand=None):

        if o is None:
            raise RuntimeError("[ERROR]: unexpected error")

        # execution of a Bar or a Chord
        if type(o) == type([]):
            o: list[Token]
            L = LeftHand
            R = RightHand
            for token in o:
                L, R = self.execute(token, L, R)
            return L, R

        # execution of a single line
        elif type(o) == type(Token("")):
            token: Token = o

            self.history.append((token, LeftHand, RightHand))
            match token.type:
                case "PLAY":  # jump
                    if type(token.content) != type(""):
                        raise RuntimeError(
                            f"[ERROR]: expected a string as the name of the jump, got {type(token.content)}")

                    if _type := self.things.get(self.format(token.content)) is None:
                        raise RuntimeError(
                            f"[ERROR]: could not find the Bar or Chord name '{self.format(token.content)}'")

                    if _type == "BAR":
                        self.execute(self.bars.get(token.content))
                        return LeftHand, RightHand
                    else:
                        self.execute(self.chords.get(token.content))
                        return LeftHand, RightHand

                case "TENUTO":
                    self.BREAK = True
                    return LeftHand, RightHand
                case "DECLARATION":
                    content: Declaration = token.content
                    if len(content.left) > 1:
                        raise RuntimeError(f"[ERROR]: expected only one token for the left side, got: {content.left}")

                    if (left_type := content.left[0].type) not in ["VARIABLE", "ARRAY_INDEX"]:
                        raise RuntimeError(f"[ERROR]: expected a variable for the left side, got {content.left[0]}")

                    if type(content.right) == type([]) and len(content.right) == 0:
                        raise RuntimeError(
                            f"[ERROR]: expected at least one token for the right side, got: {content.right}")

                    is_list = False
                    is_number = False

                    if (right_type := content.right.type) == "STRING":
                        if self.is_list_name(content.right):
                            is_list = True
                        else:
                            # is a number number
                            is_number = True
                            pass
                    elif content.right.type == "LISTEN":
                        pass
                    elif content.right.type == "ARRAY_INDEX":
                        is_list = True
                    elif content.right.type == "NUMBER":
                        raise RuntimeError(
                            f"[ERROR]: Expected a NOTE number but got a normal number on line {content.right.line}")
                    elif (right_type := content.right.type) not in ["FUNCTION",
                                                                    "VARIABLE"] and is_list is False and is_number is False:
                        raise RuntimeError(f"[ERROR]: expected a function or a variable, got: {right_type}")

                    if left_type == "VARIABLE":
                        variable_type = content.left[0].content
                        if variable_type == "LeftHand":
                            match right_type:
                                case "FUNCTION":
                                    LeftHand = self.assign(LeftHand, self.eval(content.right.content, LeftHand, RightHand, content.right.line))
                                case "STRING":
                                    if is_list:
                                        LeftHand = self.get_array_value(content.right.content, LeftHand, RightHand)
                                    elif is_number:
                                        LeftHand = self.eval(content.right.content, LeftHand, RightHand, content.right.line)
                                case "LISTEN":
                                    inp = input("> ")
                                    if len(inp) == 0:
                                        inp = " "
                                    LeftHand = ord(inp[0])
                                case "ARRAY_INDEX":
                                    LeftHand = self.check_list_name(content.right, LeftHand, RightHand)
                                case _:
                                    LeftHand = self.assign(LeftHand, content.right.content)
                        else:
                            match right_type:
                                case "FUNCTION":
                                    RightHand = self.assign(RightHand,
                                                            self.eval(content.right.content, LeftHand, RightHand, content.right.line))
                                case "STRING":
                                    if is_list:
                                        RightHand = self.get_array_value(content.right.content, LeftHand, RightHand)
                                    elif is_number:
                                        RightHand = self.eval(content.right.content, LeftHand, RightHand, content.right.line)
                                case "LISTEN":
                                    inp = input("> ")
                                    if len(inp) != 0:
                                        inp = " "
                                    RightHand = ord(inp[0])
                                case "ARRAY_INDEX":
                                    LeftHand = self.check_list_name(content.right, LeftHand, RightHand)
                                case _:
                                    RightHand = self.assign(LeftHand, content.right.content)

                        return LeftHand, RightHand
                    elif left_type == "ARRAY_INDEX":
                        index = self.check_list_name(content.left[0], LeftHand, RightHand)

                        value = 0

                        match right_type:
                            case "FUNCTION":
                                value = self.assign(LeftHand, self.eval(content.right.content, LeftHand, RightHand, content.right.line))
                            case "STRING":
                                value = self.assign(LeftHand, content.right.content)
                            case "VARIABLE":
                                value = LeftHand
                            case _:
                                raise RuntimeError("Unexpected token type")
                        self.list[index] = value
                        return LeftHand, RightHand
                case "FOR":
                    FOR: For = token.content
                    repetitions = FOR.n
                    instructions = FOR.instructions

                    for i in range(int(repetitions)):
                        LeftHand, RightHand = self.execute(instructions, LeftHand, RightHand)

                    return LeftHand, RightHand

                case "PRESS" | "PRESS_HARD" | "SMASH" | "SMASH_HARD":
                    press_statement: Token = token.content
                    value = None
                    match press_statement.type:
                        case "ARRAY_INDEX":
                            value = self.get_array_value(press_statement, LeftHand, RightHand)
                        case "STRING":
                            value = self.eval(press_statement, LeftHand, RightHand, press_statement.line)
                        case "VARIABLE":
                            value = self.get_value(press_statement, LeftHand, RightHand)
                        case _:
                            raise RuntimeError("[o]")
                    if token.type == "PRESS":
                        print(chr(value), end="")
                    elif token.type == "SMASH":
                        print(chr(value))
                    elif token.type == "SMASH_HARD":
                        print(value)
                    else:
                        print(value, end=" ")
                    return LeftHand, RightHand

                case "FORTE":
                    if_statement: If = token.content

                    left = self.get_value(if_statement.left, LeftHand, RightHand)
                    right = self.get_value(if_statement.right, LeftHand, RightHand)

                    run_then = left > right

                    if run_then:
                        if if_statement.then.type == "TENUTO":
                            self.execute(if_statement.then)
                        else:
                            self.execute(Token("PLAY", if_statement.then.content))
                    else:
                        if if_statement.has_else:
                            self.execute(Token("PLAY", if_statement.else_.content))

                    return LeftHand, RightHand

                case "PIANO":
                    if_statement: If = token.content

                    left = self.get_value(if_statement.left, LeftHand, RightHand)
                    right = self.get_value(if_statement.right, LeftHand, RightHand)

                    run_then = left < right

                    if run_then:
                        if if_statement.then.type == "TENUTO":
                            self.execute(if_statement.then)
                        else:
                            self.execute(Token("PLAY", if_statement.then.content))
                    else:
                        if if_statement.has_else:
                            if if_statement.else_.type == "TENUTO":
                                self.execute(if_statement.else_)
                            else:
                                self.execute(Token("PLAY", if_statement.else_.content))

                    return LeftHand, RightHand
                case "HARMONY":
                    if_statement: If = token.content

                    left = self.get_value(if_statement.left, LeftHand, RightHand)
                    right = self.get_value(if_statement.right, LeftHand, RightHand)

                    run_then = left == right

                    if run_then:
                        if if_statement.then.type == "TENUTO":
                            self.execute(if_statement.then)
                        else:
                            self.execute(Token("PLAY", if_statement.then.content))
                    else:
                        if if_statement.has_else:
                            if if_statement.else_.type == "TENUTO":
                                self.execute(if_statement.else_)
                            else:
                                self.execute(Token("PLAY", if_statement.else_.content))

                    return LeftHand, RightHand
                case "WHILE":
                    self.BREAK = False
                    instructions: list[Token] = token.content.instructions
                    i = 0
                    l = len(instructions)
                    while not self.BREAK:
                        self.history.append((instructions[i % l], LeftHand, RightHand))
                        LeftHand, RightHand = self.execute(instructions[i % l], LeftHand, RightHand)
                        i += 1
                    self.BREAK = False
                    return LeftHand, RightHand
                case _:
                    raise RuntimeError("[ERROR]: unknown case")
        else:
            raise RuntimeError(f"[ERROR]: unexpected thing: {o}")

    def assign(self, Variable, content: int):
        # yes, this function is completely useless, deal with it fucker
        return content

    def eval(self, content: list[str], LeftHand, RightHand, line):
        line_number = ''
        if type(content) == type(Token('')):
            line_number = content.line
        if len(content) == 1:
            if 0 < len(content[0]) < 3:
                return self.get_note_value(content[0], LeftHand, RightHand, len(content))
            else:
                if type(content) == type([]):
                    return self.eval(content[0], LeftHand, RightHand, line)

                if content[0] == "LeftHand":
                    if LeftHand is None:
                        raise RuntimeError(f"[ERROR]: init LeftHand before line {line_number}")
                    else:
                        return LeftHand
                else:

                    if content[0] != "RightHand":
                        raise RuntimeError(f"Not gonna lie, I fucked up. ")

                    if RightHand is None:
                        raise RuntimeError(f"[ERROR]: expected a value for RightHand on line {line_number}")
                    else:
                        return RightHand
        else:
            return_value = 0
            multiplication_value = 0

            note = None
            matches = None

            if type(content) == type([]):
                matches = content
            elif type(content) == type(""):
                matches = re.findall(r"(([a-gA-GLR]#*)|(,))", content)
                matches = [m[0] for m in matches]
            elif type(content) == type(Token("", )):
                if content.type != "STRING" and content.type != "VARIABLE":
                    raise RuntimeError(f"Unexpected error on line {line_number}")
                if content.type == "VARIABLE":
                    matches = [content.content]
                else:
                    matches = re.findall(r"(([a-zA-Z]#*)|(,))", content.content)
                    matches = [m[0] for m in matches]
            else:
                raise RuntimeError("Error...")

            start = 0
            if len(matches) > 1:
                start = 1

            for i in range(start, len(matches)):
                prev_note = matches[i - 1]
                note = matches[i]

                if note != ",":
                    if prev_note == "," and i == start:
                        raise ParseException(f"[ERROR]: can't start a note number with ',' on line {line_number}")
                    elif prev_note == ",":
                        continue
                    # multiplication
                    if multiplication_value == 0:
                        multiplication_value = self.get_note_value(prev_note, LeftHand, RightHand, line_number)
                    else:
                        multiplication_value *= self.get_note_value(prev_note, LeftHand,
                                                                    RightHand, line_number)
                else:
                    # multiplication
                    if multiplication_value == 0:
                        multiplication_value = self.get_note_value(prev_note, LeftHand, RightHand, line_number)
                    else:
                        multiplication_value *= self.get_note_value(prev_note, LeftHand,
                                                                    RightHand, line_number)
                    return_value += multiplication_value
                    multiplication_value = 0

            if note == ",":
                raise RuntimeError("[ERROR]: can't have ',' as a last statement on a line")
            elif len(matches) != 1:
                if multiplication_value != 0:
                    return_value += multiplication_value * self.get_note_value(note, LeftHand, RightHand,
                                                                               line_number=line_number)
                else:
                    return_value += self.get_note_value(note, LeftHand, RightHand, line_number=line_number)
            else:
                if multiplication_value != 0:
                    return_value += multiplication_value
                else:
                    pass
            return return_value

    def get_note_value(self, note: str | Token, LeftHand, RightHand, line_number: int) -> int:
        if len(note) == 0:
            raise RuntimeError(f"[ERROR]: expected a string with at least one element")
        num_hashtags = 0
        if type(note) == type(Token("")):
            note = [note.content]
            num_hashtags = len(re.findall(r"(#)", note[0]))
        else:
            num_hashtags = len(re.findall(r"(#)", note))
            note = note.replace(" ", "").replace("#", "")

        match note[0].replace(" ", "").replace("#", ""):
            case "C":
                return 0 + num_hashtags
            case 'D':
                return 2 + num_hashtags
            case "E":
                return 4 + num_hashtags
            case "F":
                return 6 + num_hashtags
            case "G":
                return 8 + num_hashtags
            case "A":
                return 10 + num_hashtags
            case "B":
                return 12 + num_hashtags

            case "c":
                return -(0 + num_hashtags)
            case "d":
                return -(2 + num_hashtags)
            case "e":
                return -(4 + num_hashtags)
            case "f":
                return -(6 + num_hashtags)
            case "g":
                return -(8 + num_hashtags)
            case "a":
                return -(10 + num_hashtags)
            case "b":
                return -(12 + num_hashtags)

            case "LeftHand" | "L":
                if LeftHand is None:
                    raise RuntimeError(f"[ERROR]: LeftHand has no value on line {line_number}")
                return LeftHand
            case "RightHand" | "R":
                if RightHand is None:
                    raise RuntimeError(f"[ERROR]: RightHand has no value on line {line_number}")
                return RightHand
            case " ":
                # ignore spaces
                pass
            case ",":
                raise RuntimeError(f"[ERROR]: unexpected ',' on line {line_number}")
            case _:
                raise RuntimeError(f"[ERROR]: '{note}' is not a valid note on line {line_number}")

    def is_list_name(self, token: Token):
        if token.type != "STRING":
            raise RuntimeError("[ERROR]: expected a string for the name of the list")

        if token.content.replace(" ", "") != self.list_name.replace(" ", ""):
            return False

        return True

    def check_list_name(self, token: Token, L, R):
        if type(token.content) != type([]):
            raise RuntimeError("[ERROR]: fucker")
        if len(token.content) < 2:
            raise RuntimeError("[ERROR]: fucker 2")
        if token.content[0].type != "STRING":
            raise RuntimeError("[ERROR: fucker 3")
        if token.content[0].content.replace(" ", "") != self.list_name.replace(" ", ""):
            raise RuntimeError(f"[ERROR]:|{token.content[0].content.replace(' ', '')}| != |{self.list_name.replace(' ', '')}|")

        return self.get_note_value(token.content[1], L, R, token.content[0].line)

    def get_array_value(self, content, L, R):
        value = self.check_list_name(content, L, R)
        if (v := self.list.get(value)) is None:
            raise RuntimeError(f"[ERROR]: list at index {value} is not defined")
        else:
            return v

    def evaluate_condition(self, condition: Token, LeftHand, RightHand):
        equals = condition.content.content

        if condition.type == "CONDITION":
            left = equals[0][0]
            right = equals[1][0]
            return self.get_note_value(left.content, LeftHand, RightHand, left.line) == self.get_note_value(right.content,
                                                                                                 LeftHand, RightHand, right.line)
        else:
            left = equals[0][0]
            return self.get_note_value(left.content, LeftHand, RightHand, left.line)

    def get_value(self, left: Token, LeftHand, RightHand):
        l = None
        if type(left) == type("string"):
            left = Token("STRING", left)

        match left.type:
            case "ARRAY_INDEX":
                l = self.get_array_value(left, LeftHand, RightHand)
            case "STRING":
                l = self.eval(left.content, LeftHand, RightHand, left.line)
            case "VARIABLE":
                if left.content == "LeftHand":
                    if LeftHand is None:
                        raise RuntimeError("[ERROR]: please first initialize the Lefthand before using it (it has no "
                                           "value)")
                    else:
                        l = LeftHand
                else:
                    if RightHand is None:
                        raise RuntimeError("[ERROR]: please first initialize the RightHand before using it (it has no "
                                           "value)")
                    else:
                        l = RightHand
            case _:
                raise RuntimeError(f"[ERROR]: unexpected type for value, got {left.type}")
        return l

    def format(self, name: str):
        return re.sub(r" $", "", name)

if __name__ == '__main__':
    pass
