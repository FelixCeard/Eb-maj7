import argparse

from maj7.executer import Executor
from maj7.lexer import Lexer
from maj7.parser import Parser


def run():
    try:
        parser = argparse.ArgumentParser(description='Run any maj7 file')
        parser.add_argument('path', type=str, help="The path to the maj7 file")
        args = parser.parse_args()

        program = None

        with open(args.path, 'r') as file:
            program = '\n'.join(file.readlines())

        lexer = Lexer(program)

        tokens = lexer.lex()

        parser = Parser(tokens)

        Executor(parser.parse_tokens)
    except Exception as e:
        print(e)


if __name__ == '__main__':
    run()
