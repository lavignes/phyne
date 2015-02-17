from phyne import Lexer, token, LexerError

code = '''\
// Greatest Common Divisor
x := 8;
y := 12;
WHILE x != y DO
  IF x > y THEN x := x-y
    ELSE y := y-x
  FI
OD;
PRINT x
'''

class LexerErrorWithLineNo(LexerError):
    def __init__(self, message, line_no):
        super(LexerErrorWithLineNo, self).__init__(message)
        self.line_no = line_no

class BasicLexer(Lexer):
    def __init__(self, input_data, *args, **kwargs):
        super(BasicLexer, self).__init__(input_data, *args, **kwargs)
        self.line_no = kwargs.get('line_no', 1)

    def error_with_message(self, message):
        return LexerErrorWithLineNo(message, self.line_no)

    def error_for_input(self, bad_input):
        message = 'Unexpected input: \'{}\''.format(bad_input)
        return self.error_with_message(message)

    @token(r'//.*?\n')
    def comment(self, text):
        self.line_no += 1

    @token(r'\n')
    def newlines(self, text):
        self.line_no += 1

    @token(r'\s')
    def other_whitespace(text):
        pass

    @token(r'=')
    def eq(text):
        return text

    @token(r'!=')
    def neq(text):
        return text

    @token(r'<=')
    def le(text):
        return text

    @token(r'<')
    def lt(text):
        return text

    @token(r'>=')
    def ge(text):
        return text

    @token(r'>')
    def gt(text):
        return text

    @token(r'\+')
    def plus(text):
        return text

    @token(r'-')
    def minus(text):
        return text

    @token(r'\*')
    def mult(text):
        return text

    @token(r'\/')
    def div(text):
        return text

    @token(r'\(')
    def open_paren(text):
        return text

    @token(r'\)')
    def close_paren(text):
        return text

    @token(r':=')
    def assign(text):
        return text

    @token(r';')
    def semi(text):
        return text

    @token(r'IF\b')
    def t_if(text):
        return text

    @token(r'THEN\b')
    def t_then(text):
        return text

    @token(r'ELSE\b')
    def t_else(text):
        return text

    @token(r'FI\b')
    def t_fi(text):
        return text

    @token(r'WHILE\b')
    def t_while(text):
        return text

    @token(r'DO\b')
    def t_do(text):
        return text

    @token(r'OD\b')
    def t_od(text):
        return text

    @token(r'PRINT\b')
    def t_print(text):
        return text

    @token(r'[0-9]+')
    def number(text):
        return int(text)

    @token(r'[a-z]')
    def name(text):
        return text


try:
    for token in BasicLexer(code):
        print token

except LexerErrorWithLineNo as e:
    print 'Error On Line:{}: {}'.format(e.line_no, e.message)
    exit(1)