import inspect, re, sys, io
from collections import namedtuple

def token(regular_expression, **kwargs):
    '''Injects a 'token_info' property into a method'''
    def token_decorator(func):
        code = None

        # Python3 compat
        if hasattr(func, '__code__'):
            code = func.__code__
        else:
            code = func.func_code   

        func.token_info = {
            'state': kwargs.get('state'),
            'regular_expression': regular_expression,
            'passes_self': 'self' in code.co_varnames,
            'line_no': code.co_firstlineno
        }
        return func
    return token_decorator

Token = namedtuple('Token', ['name', 'value'])

class LexerError(Exception):
    def __init__(self, message):
        super(LexerError, self).__init__(message)
        # Python 3 compat, Exception no longer has 'message'
        self.message = message

class Lexer(object):
    __regex = None
    __lexemes = None

    def __new__(cls, *args, **kwargs):
        obj = super(Lexer, cls).__new__(cls)
        if cls.__lexemes is None:

            # Sort methods by the line number they were defined on.
            # We could use an ordered class in python 3 and do this
            # entire method in __prepare__.
            def get_line_number(member_tuple):
                member = member_tuple[1]
                if inspect.ismethod(member):
                    func = member.__func__
                    if hasattr(func, 'token_info'):
                        return func.token_info['line_no']
                return 0

            members = sorted(inspect.getmembers(cls), key=get_line_number)

            cls.__lexemes = {}
            groups = []
            for name, method in members:
                if hasattr(method, 'token_info'):
                    cls.__lexemes[name] = method
                    regular_expression = method.token_info['regular_expression']
                    group = '(?P<{}>{})'.format(name, regular_expression)
                    groups.append(group)

            full_expression = '|'.join(groups)
            cls.__regex = re.compile(full_expression, re.UNICODE | re.MULTILINE)

        return obj

    def __init__(self, input_data, *args, **kwargs):
        self._prev_lexer = None
        self._next_lexer = None
        self._index = 0

        # Python3 compat
        def is_str(obj):
            try:
                return isinstance(obj, basestring)
            except NameError:
                return isinstance(obj, str)

        # Python3 compat
        def is_file(obj):
            if isinstance(obj, io.IOBase):
                return True
            elif isinstance(obj, file):
                return True
            return False

        if is_file(input_data):
            self._text = input_data.read()   
        elif is_str(input_data):
            self._text = input_data
        elif isinstance(input_data, Lexer):
            # Inherit the attributes of our outer lexer
            self._text = input_data._text
            self._index = input_data._index

    def __iter__(self):
        return self

    def error_for_input(self, bad_input):
        return LexerError(bad_input)

    # Python3 compat
    def __next__(self):
        return self.next()

    def next(self):
        while True:
            if self._next_lexer is not None:
                value = next(self._next_lexer)
                if value is not None:
                    return value
                # Inner lexer emitted None, it is dead now
                # If this inner lexer is lexing our input, we must reset the
                # input index
                if self._next_lexer._text is self._text:
                    self._index = self._next_lexer._index
                self._next_lexer = None

            match_object = self.__class__.__regex.match(self._text, self._index)
            if match_object is not None:
                name = match_object.lastgroup
                text = match_object.group(name)
                self._index = match_object.end()
                method = self.__class__.__lexemes[name]

                # Allows the user to use static methods or
                # instance methods as their token matcher
                if method.token_info['passes_self']:
                    value = method(self, text)
                else:
                    # Python3 compat
                    try:
                        value = method(text)
                    except (TypeError, UnboundLocalError):
                        value = method.__func__(text)

                # If a token returns itself, we are exiting an child lexer
                if value is self:
                    return None

                # If a token returns a lexer, we will emit tokens from it
                elif isinstance(value, Lexer):
                    self._next_lexer = value
                    value._prev_lexer = self
                    continue

                elif value is not None:
                    return Token(name, value)

            # Not at end of input but I see a weird token
            elif self._index != len(self._text):
                raise self.error_for_input(self._text[self._index])

            else:
                # End of input but I have a parent lexer
                if self._prev_lexer:
                    return None
                raise StopIteration
