import re

from .utils import *


class Parser:

    def __init__(self, tokens):
        self.tokens = tokens
        self.parse_tokens = []

        i = self.parse_header()
        self.parse_lines(self.tokens[i:])

    def parse_header(self):
        has_time = False  # 5. Line
        has_opening = False

        parse_tokens = []

        i = 0

        for line_number, line in enumerate(self.tokens):
            # Parse header
            if line_number == 0:
                if len(line) == 3:
                    token = line[0]
                    if token.type != "STRING":
                        raise ParseException(f"[ERROR]: Expected a String as a title, got {token.type}")
                    else:
                        parse_tokens.append(Token("TITLE", token.content, line=token.line))

                    token = line[1]
                    if token.type != "IN":
                        raise ParseException(f"[ERROR]: Expected 'in' between title and key, got {token.type}")

                    token = line[2]
                    if token.type != "STRING":
                        raise ParseException(f"[ERROR]: Expected 'in' between title and key, got {token.type}")
                    else:
                        parse_tokens.append(Token("KEY", token.content, line=token.line))

                else:
                    raise ParseException(
                        f"Unexpected amount of tokens on line {line[0].line}: {self.line_to_string(line)}\n")

            elif line_number == 1:  # 2. line => author
                if len(line) == 1:
                    token = line[0]
                    if token.type != "STRING":
                        raise ParseException(f"[ERROR]: Expected a String as a author, got {token.type}")
                    else:
                        parse_tokens.append(Token("AUTHOR", token.content, line=token.line))
                else:
                    raise ParseException(f"[ERROR]: Expected one token on line 2, got {len(line)}")

            elif line_number == 2:
                token = line[0]
                if token.type != "COMPOSED":
                    raise ParseException(f"[ERROR]: Expected a the keyword 'composed' on line 3, got {token.content}")

                token = line[1]
                if token.type != "IN":
                    raise ParseException(f"[ERROR]: Expected 'in' between composed and year, got {token.type}")

                token = line[2]
                if token.type != "NUMBER":
                    raise ParseException(f"[ERROR]: Expected a number for the year, got {token.type}")
                else:
                    parse_tokens.append(Token("YEAR", int(token.content), line=token.line))

            elif line_number == 3:  # very important
                if len(line) < 3:
                    raise ParseException(f"[ERROR]: Expected 3 tokens where you name the list")

                token = line[0]
                if token.type != "COMPOSED":
                    raise ParseException(f"[ERROR]: Expected a the keyword 'composed' on line 3, got {token.content}")

                token = line[1]
                if token.type != "IN":
                    raise ParseException(f"[ERROR]: Expected 'in' between composed and year, got {token.type}")

                token = line[-1]  # last
                if token.type != "STRING":
                    raise ParseException(f"[ERROR]: Expected a string for the list, got {token.type}")
                else:
                    parse_tokens.append(Token("LIST_NAME", token.content.split(" ")[-2], line=token.line))
            else:
                if not has_time:
                    if len(line) == 3:
                        token = line[0]
                        if token.type != "TIME":
                            raise ParseException(f"[ERROR]: Expected the time keyword to set the tempo {token.type}")

                        token = line[1]
                        if token.type != "SPECIAL":
                            raise ParseException(f"[ERROR]: Expected ':' after time {token.type}")

                        token = line[2]
                        if token.type != "NUMBER":
                            raise ParseException(f"[ERROR]: Expected a number for the tempo {token.type}")
                        else:
                            parse_tokens.append(Token("TEMPO", token.content, line=token.line))

                        has_time = True
                    else:
                        raise ParseException(f"[ERROR]: Expected a 3 tokens, got {len(line)}")

                elif not has_opening:
                    if len(line) != 3:
                        raise ParseException(f"[ERROR]: Expected at least 3 tokens, got {len(line)}")

                    token = line[0]
                    if token.type != "OPENING":
                        raise ParseException(
                            f"[ERROR]: Expected the keyword 'opening' to set the opening bar {token.type}")

                    token = line[1]
                    if token.type != "IN":
                        raise ParseException(f"[ERROR]: Expected in after 'opening' {token.type}")

                    token = line[2]
                    if token.type != "STRING":
                        raise ParseException(f"[ERROR]: a string for the name of the opening bar {token.type}")
                    else:
                        parse_tokens.append(Token("OPENING", token.content, line=token.line))

                    has_opening = True

                    self.parse_tokens = parse_tokens

                    i = line_number + 1
                    break
                else:
                    raise ParseException(f"[ERROR]: unexpected reach of code.")
        return i

    def parse_lines(self, lines):
        if len(lines) == 0:
            return

        line = lines[0]
        if len(line) == 0:
            return

        match line[0].type:
            case "BAR":
                if len(line) != 3:
                    raise ParseException(f"[ERROR]: expected 3 tokens, got {len(line)}")
                if line[1].type != "SPECIAL" and line[1].content != ":":
                    raise ParseException(f"[ERROR]: need ':' after Bar declaration")
                if line[2].type != "STRING":
                    raise ParseException(f"[ERROR]: a Bar name should be a string, not {line[2].type}")
                else:
                    return self.parse_bar(lines[1:], line[2].content)

            case "CHORD":
                if len(line) != 3:
                    raise ParseException(f"[ERROR]: expected 3 tokens, got {len(line)}")
                if line[1].type != "SPECIAL" and line[1].content != ":":
                    raise ParseException(f"[ERROR]: need ':' after Chord declaration")
                if line[2].type != "STRING":
                    raise ParseException(f"[ERROR]: a Chord name should be a string, not {line[2].type}")
                else:
                    return self.parse_chord(lines[1:], line[2].content)

            case _:
                raise ParseException("[ERROR]: you need to write code inside a Chord or a Bar")

    def parse_bar(self, lines: list[list[Token]], name, instructions=None):
        if instructions is None:
            instructions = []

        if len(lines) == 0:
            self.parse_tokens.append(Token("BAR", Section(name, instructions, "BAR"), int(instructions[0].line) - 1))

        for i, line in enumerate(lines):
            if len(line) > 0:
                if line[0].type in ["BAR", "CHORD"]:
                    self.parse_tokens.append(
                        Token("BAR", Section(name, instructions, "BAR"), int(instructions[0].line) - 1))
                    return self.parse_lines(lines[i:])

                elif line[0].type == "NUMBER":
                    if line[1].type != "LOOP_START":
                        raise ParseException("[ERROR]: no loop is being started after the initial call")

                    new_list, new_instructions = self.parse_for(lines[i:], line[0].content, instructions, "BAR", name)
                    return self.parse_bar(new_list, name, new_instructions)
                elif line[0].type == "LOOP_START":
                    new_list, new_instructions = self.parse_while(lines[i:], instructions, "BAR", name)
                    return self.parse_bar(new_list, name, new_instructions)

                elif line[0].type == "SPECIAL" and line[0].content == "#":
                    # skip the line
                    pass
                else:
                    instructions.append(self.parse_line(line))

        # end of file
        self.parse_tokens.append(Token("BAR", Section(name, instructions, "BAR"), int(instructions[0].line) - 1))

    def parse_chord(self, lines, name, instructions=None):
        if instructions is None:
            instructions = []

        for i, line in enumerate(lines):
            if len(line) > 0:
                if line[0].type in ["BAR", "CHORD"]:
                    self.parse_tokens.append(
                        Token("CHORD", Section(name, instructions, "CHORD"), int(instructions[0].line) - 1))
                    return self.parse_lines(lines[i:])

                elif line[0].type == "NUMBER":
                    if line[1].type != "LOOP_START":
                        raise ParseException("[ERROR]: no loop is being started after the initial call")
                    new_list, new_instructions = self.parse_for(lines[i:], line[0].content, instructions, "CHORD", name)
                    return self.parse_chord(new_list, name, new_instructions)
                elif line[0].type == "LOOP_START":
                    new_list, new_instructions = self.parse_while(lines[i:], instructions, "BAR", name)
                    return self.parse_bar(new_list, name, new_instructions)
                elif line[0].type == "SPECIAL" and line[0].content == "#":
                    # skip the line
                    pass
                else:
                    instructions.append(self.parse_line(line))

        # end of file
        self.parse_tokens.append(Token("CHORD", Section(name, instructions, "CHORD"), int(instructions[0].line) - 1))

    def parse_right(self, line: list[Token]) -> Token:
        left_side = []
        for index, token in enumerate(line):
            if token == None:
                continue

            if token.type == "SPECIAL" and token.content == "/":
                if len(left_side) > 2:
                    raise ParseException("[ERROR]: What are you doing? left should be the name of the list")
                elif len(left_side) == 1:
                    left_side = [Token("ARRAY_INDEX", [left_side[0], line[index + 1]], token.line)]
                    line[index + 1] = None
                else:
                    raise RuntimeError("[ERROR]: unexpected use of '/'")
            else:
                left_side.append(token)

        if len(left_side) > 1:
            raise ParseException(f"[ERROR]: Expected only one token, got {len(left_side)}")
        return left_side[0]

    def parse_line(self, line: list[Token]) -> Token:
        if len(line) > 0:
            if line[0].type == "PLAY":
                if len(line) != 2:
                    raise ParseException(
                        f"[ERROR]: you need to play with something, but not too much either! Unexpected amount of token on line {line[0].line}")
                else:
                    if line[1].type == "STRING":
                        return Token("PLAY", line[1].content, line[1].line)
                    else:
                        raise ParseException("[ERROR]: the name should be a string")
            elif line[0].type == "PRESS":
                if len(line) == 1:
                    raise ParseException("[ERROR]: can't print nothing")
                if len(line) > 2:
                    if line[1].type == "HARD":
                        return Token("PRESS_HARD", self.parse_right(line[2:]), line[1].line)
                return Token("PRESS", self.parse_right(line[1:]), line[0].line)

            elif line[0].type == "SMASH":
                if len(line) == 1:
                    return Token("SMASH", [], line[0].line)
                if len(line) > 2:
                    if line[1].type == "HARD":
                        return Token("SMASH_HARD", self.parse_right(line[2:]), line[0].line)
                return Token("SMASH", self.parse_right(line[1:]), line[0].line)
            elif line[0].type == "LOOP_START":
                raise ParseException("[ERROR]: shouldn't run this code")
            elif line[0].type == "FORTE":
                if len(line) == 5:
                    # forte a b play str
                    # forte a b tenuto tenuto
                    if line[3].type == "TENUTO" and line[4].type == "TENUTO":
                        # raise ParseException("[ERROR]: something's missing")
                        _if = If(line[1], line[2], line[3], line[4])
                        return Token("FORTE", _if, line[0].line)
                    else:
                        return Token("FORTE", If(line[1], line[2], line[4]), line[0].line)
                elif len(line) == 8:
                    # forte a b play str piano play str
                    _if = If(line[1], line[2], line[4], line[7])
                    return Token("FORTE", _if, line[0].line)
                elif len(line) == 4:
                    # forte a b tenuto
                    if line[3].type != "TENUTO":
                        raise ParseException("[ERROR]: something's missing")
                    _if = If(line[1], line[2], line[3], None)
                    return Token("FORTE", _if, line[0].line)
                elif len(line) == 7:
                    # forte a b tenuto piano play _
                    # forte a b play _ piano tenuto
                    if line[3].type == "TENUTO":
                        _if = If(line[1], line[2], line[3], line[6])
                    else:
                        _if = If(line[1], line[2], line[4], line[6])
                    return Token("FORTE", _if, line[0].line)
                else:
                    raise ParseException("[ERROR]: expected this 'forte a b play s [piano play s]'")
            elif line[0].type == "PIANO":
                if len(line) == 5:
                    # piano a b play str
                    return Token("PIANO", If(line[1], line[2], line[4]), line[0].line)
                elif len(line) == 8:
                    # piano a b play str forte play str
                    _if = If(line[1], line[2], line[4], line[7])
                    return Token("PIANO", _if, line[0].line)
                else:
                    raise ParseException("[ERROR]: expected this 'piano a b play s [forte play s]'")

            elif line[0].type == "HARMONY":
                if len(line) == 5:
                    # harmonizes a b play str
                    return Token("HARMONY", If(line[1], line[2], line[4]), line[0].line)
                elif len(line) == 8:
                    # harmonizes a b play str [forte, piano] play str
                    _if = If(line[1], line[2], line[4], line[7])
                    return Token("HARMONY", _if, line[0].line)
                else:
                    raise ParseException("[ERROR]: expected this 'harmonizes a b play s [[forte, piano] play s]'")

            else:
                left_side = []
                for index, token in enumerate(line):
                    if token == None:
                        continue
                    if token.type == "SPECIAL" and token.content == "/":
                        if len(left_side) > 1:
                            raise ParseException("[ERROR]: What are you doing? left should be the name of the list")
                        left_side = [Token("ARRAY_INDEX", [left_side[0], line[index + 1]], left_side[0].line)]
                        line[index + 1] = None
                    elif token.type == "SPECIAL" and token.content == "=":
                        raise RuntimeError(
                            f"[ERROR]: Expected ':=' but got '=' on line {line[0].line} ({self.line_to_string(line)})")
                    elif token.type not in ["DECLARATION", "NUMBER"]:
                        left_side.append(token)
                    else:
                        match token.type:
                            case "DECLARATION":
                                return Token("DECLARATION",
                                             Declaration(left_side, self.check_for_values(line[index + 1:])),
                                             line[0].line)
                            case "NUMBER":
                                return token
                            case _:
                                raise RuntimeError("[ERROR]: unexpected token type")

                raise RuntimeError(f"[ERROR]: Expected more code on line {line[0].line}: {self.line_to_string(line)}")

    def parse_for(self, lines: list[list[Token]], n: int, instructions: list[Token], type: str, name: str):
        for_instructions = []

        for i in range(1, len(lines)):
            line = lines[i]
            if len(line) > 0:
                match line[0].type:
                    case "CHORD":
                        raise ParseException(
                            "[ERROR]: can't start a Chord inside a for loop, maybe you forgot the ':|'")
                    case "BAR":
                        raise ParseException("[ERROR]: can't start a Bar inside a for loop, maybe you forgot the ':|'")
                    case "LOOP_END":
                        if len(for_instructions) > 0:
                            f = Token("FOR", For(n, for_instructions), for_instructions[0].line)
                        else:
                            f = Token("FOR", For(n, for_instructions), line[0].line)
                        instructions.append(f)
                        return lines[i + 1:], instructions
                    case _:
                        if r := self.parse_line(line):
                            for_instructions.append(r)

    def check_for_values(self, s: list[Token]):
        for i, token in enumerate(s):
            if token.type == "STRING":
                match = re.match(r"(?![a-fA-F, ]+|LeftHand|RightHand)(.)", token.content)
                if match is None:
                    return Token("FUNCTION", self.string_to_array(token.content), token.line)
            if token.type == "SPECIAL" and token.content == "#":  # end of line comments
                return self.parse_right(s[:i])
        return self.parse_right(s)

    def string_to_array(self, string: str):
        string = string.replace("LeftHand", "L").replace("RightHand", "R")
        m = re.findall(r"(([a-gA-GLR]#*)|(,))", string)

        l = [triple[0] for triple in m]
        return l

    def parse_condition(self, condition: list[Token]) -> Token:
        left = []
        if len(condition) == 1:
            return condition[0]
        for i, token in enumerate(condition):
            if token.type != "EQUALS":
                left.append(token)
            else:
                return Token("EQUALS", [left, self.check_right(condition[i + 1:])], token.line)

        raise ParseException("[ERROR]: unexpected tokens")

    def check_right(self, param: list[Token]):
        l = []
        for token in param:
            if token.type == "EQUALS":
                raise ParseException("[ERROR]: unexpected tokens")
            l.append(token)

        return l

    def parse_while(self, lines, instructions, param1, name):
        while_instructions = []

        for i in range(1, len(lines)):
            line = lines[i]
            if len(line) > 0:
                match line[0].type:
                    case "CHORD":
                        raise ParseException(
                            "[ERROR]: can't start a Chord inside a for loop, maybe you forgot the ':|'")
                    case "BAR":
                        raise ParseException("[ERROR]: can't start a Bar inside a for loop, maybe you forgot the ':|'")
                    case "LOOP_END":
                        f = Token("WHILE", For(0, while_instructions), line[0].line)
                        instructions.append(f)
                        return lines[i + 1:], instructions
                    case _:
                        if r := self.parse_line(line):
                            while_instructions.append(r)

    def line_to_string(self, line: list[Token]):
        string = [token.content for token in line]
        return ' '.join(string)

if __name__ == '__main__':
    pass
