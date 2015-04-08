This documentation is terrible! I'll improve it when I get some free time.
Or... feel free to fix it for me. :)

Even without good documentation, Phyne is ludicrously simple to use!

## Installing:

Use distutils to install:

`$ python setup.py install`

## Running:

Let's start with a basic lexer
```python

from phyne import Lexer, token

class CalculatorLexer(Lexer):

  @token(r'\s')
  def whitespace(text):
    pass

  @token(r'[0-9]+')
  def integer(text):
    return int(text)

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
  def paren_open(text):
    return text

  @token(r'\)')
  def paren_close(text):
    return text

for token in CalculatorLexer('(5 + 13) / 4 * 3 - 71'):
  print token

```

Output:

```
Token(name='paren_open', value='(')
Token(name='integer', value=5)
Token(name='plus', value='+')
Token(name='integer', value=13)
Token(name='paren_close', value=')')
Token(name='div', value='/')
Token(name='integer', value=4)
Token(name='mult', value='*')
Token(name='integer', value=3)
Token(name='minus', value='-')
Token(name='integer', value=71)
```

## Getting real:

OK. Thats neat. But we want to tokenize some complex stuff.
What about a programming language?

Let's tokenize some basic-like code, and expand from there:
```
// Greatest Common Divisor
x := 8;
y := 12;
WHILE x != y DO
  IF x > y THEN
    x := x-y
  ELSE
    y := y-x
  FI
OD;
PRINT x
```

First we'll start with the easy bits. And since this is a programming language
we should add line-number tracking so we can print useful debug messages.

```python
from phyne import Lexer, token, LexerError

code = '''\
// Greatest Common Divisor
x := 8;
y := 12;
WHILE x != y DO
  IF x > y THEN
    x := x-y
  ELSE
    y := y-x
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

    def error_for_input(self, bad_input):
        message = 'Unexpected input: \'{}\''.format(bad_input)
        return LexerErrorWithLineNo(message, self.line_no)

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
```

This will tokenize strings of basic just fine. But lets add the ability
to analyze real files. The lexer class already supports being constructed with
a file.

```python
from phyne import Lexer, token, LexerError

class LexerErrorWithLineNo(LexerError):
    # Errors now contain the filename
    def __init__(self, message, filename, line_no):
        super(LexerErrorWithLineNo, self).__init__(message)
        self.filename = filename
        self.line_no = line_no

class BasicLexer(Lexer):
    def __init__(self, input_data, *args, **kwargs):
        super(BasicLexer, self).__init__(input_data, *args, **kwargs)
        self.line_no = kwargs.get('line_no', 1)
        self.filename = input_data.name # Save filename!

    def error_with_message(self, message):
        return LexerErrorWithLineNo(message, self.filename, self.line_no)

    def error_for_input(self, bad_input):
        message = 'Unexpected input: \'{}\''.format(bad_input)
        return self.error_with_message(message)

    # Same tokens as before ....

# Create a file for us to parse
with open('code.bas', 'w') as codefile:
    codefile.write('''
        // Greatest Common Divisor
        x := 8;
        y := 12;
        WHILE x != y DO
          IF x > y THEN x := x-y
            ELSE y := y-x
          FI
        OD;
        PRINT
        ''')

try:
    # Pass a file to the lexer instead
    for token in BasicLexer(open('code.bas', 'r')):
        print token

except LexerErrorWithLineNo as e:
    # Print more useful error!
    print '{}:{}: {}'.format(e.filename, e.line_no, e.message)
    exit(1)