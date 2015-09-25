import re, io, unittest
from collections import OrderedDict, namedtuple

Token = namedtuple('Token', ['name', 'value'])

def token(regex, *args, custom_name=None, **kwargs):
    if regex is None:
        raise ValueError('regex cannot be None')
    if not isinstance(regex, str):
        raise ValueError('regex must be a string')
    try:
        re.compile(regex)
    except re.error:
        raise ValueError('regex must be a valid regular expression')
    def token_decorator(method):
        method.token_regex = regex
        method.token_name = custom_name or method.__name__
        return method
    return token_decorator

class LexerError(Exception):
    def __init__(self, lexer):
        self._lexer = lexer

    @property
    def lexer(self):
        return self._lexer

class _OrderedClass(type):
    @classmethod
    def __prepare__(metacls, name, bases, *args, **kwargs):
        return OrderedDict()

    def __new__(cls, name, bases, namespace, *args, **kwargs):
        result = type.__new__(cls, name, bases, dict(namespace), *args, **kwargs)
        result.members = tuple(namespace)
        return result

class Lexer(metaclass=_OrderedClass):
    __regex = None

    def __new__(cls, *args, **kwargs):
        obj = super(Lexer, cls).__new__(cls)

        # We've already compiled the rexgex, skip
        if cls.__regex is not None:
            return obj

        # Create pipe-delimited list of named groups
        regex = '|'.join('(?P<{}>{})'.format(name, method.token_regex) \
            for name, method in cls.__dict__.items() \
            if hasattr(method, 'token_regex'))
        cls.__regex = re.compile(regex, re.MULTILINE | re.UNICODE)

        return obj

    def __init__(self, input_data, *args, error_class=LexerError, **kwargs):
        if input_data is None:
            raise ValueError('input_data cannot be None')
        if not issubclass(error_class, LexerError):
            raise ValueError('error_class must be subclass of LexerError')

        self._parent_lexer = None
        self._child_lexer = None
        self._offset = 0
        self._error_class = error_class

        # If input_data is a lexer, we continue lexing where it left off
        if isinstance(input_data, Lexer):
            self._text = input_data._text
            self._offset = input_data._offset
        elif isinstance(input_data, io.IOBase):
            self._text = input_data.read()
        elif isinstance(input_data, str):
            self._text = input_data
        else:
            raise ValueError('input_data must be a Lexer, file, or string')

    @property
    def offset(self):
        return self._offset

    @property
    def parent_lexer(self):
        return self._parent_lexer

    @property
    def error_class(self):
        return self._error_class

    def __iter__(self):
        return self

    def __next__(self):
        while True:
            if self._child_lexer is not None:
                value = next(self._child_lexer)
                if value is not None:
                    return value
                # Child lexer emitted None, it is out of tokens
                # We regain control by lexing from where it left off
                if self._child_lexer._text is self._text:
                    self._offset = self._child_lexer._offset
                self._child_lexer = None

            match = self.__class__.__regex.match(self._text, self._offset)
            if match is None:
                # Unexpected input, but we aren't at the end of input
                if self._offset != len(self._text):
                    raise self._error_class(self)
                # Return None to give control back to our parent if we can
                if self._parent_lexer is not None:
                    return None
                # No more tokens (end of input)
                raise StopIteration

            name = match.lastgroup
            text = match.group(name)
            self._offset = match.end()
            method = getattr(self, name)
            value = method(text)

            # If a token matcher returns its own Lexer, we return to our parent
            if value is self:
                return None

            # If a token matcher returns None, we ignore the token
            if value is None:
                continue

            # If value is a Lexer class, we will instanciate it
            if isinstance(value, type) and issubclass(value, Lexer):
                lexer = value(self, error_class=self._error_class)
                self._child_lexer = lexer
                lexer._parent_lexer = self
                continue

            return Token(method.token_name, value)

class TestLexer(unittest.TestCase):
    @staticmethod
    def simple_t_lexer(regex, *args, skip=None, **kwargs):
        class SimpleLexer(Lexer):
            @token(regex, *args, **kwargs)
            def t(self, text):
                if text == skip:
                    return None
                return text
        return SimpleLexer

    @staticmethod
    def simple_t_sub_lexer(start_regex, inner_regex, end_regex):
        class InnerLexer(Lexer):
            @token(inner_regex)
            def t(self, text):
                return text

            @token(end_regex)
            def end(self, text):
                return self

        class StartLexer(Lexer):
            @token(start_regex)
            def start(self, text):
                return InnerLexer
        return StartLexer

    def test_token_exceptions(self):
        self.assertRaises(ValueError, self.simple_t_lexer, None)
        self.assertRaises(ValueError, self.simple_t_lexer, 42)
        self.assertRaises(ValueError, self.simple_t_lexer, '[bad_regex[')

    def test_regex(self):
        SimpleLexer = self.simple_t_lexer(r'expr')
        lexer = SimpleLexer('')
        self.assertIsInstance(lexer, Lexer)
        self.assertIn(r'(?P<t>expr)', lexer._Lexer__regex.pattern)

    def test_lexer_init_exceptions(self):
        SimpleLexer = self.simple_t_lexer(r'expr')
        self.assertRaises(ValueError, SimpleLexer, None)
        self.assertRaises(ValueError, SimpleLexer, 42)
        self.assertRaises(ValueError, SimpleLexer, '', error_class=Exception)

    def test_lexer_simple_init(self):
        class MyLexerError(LexerError):
            pass
        SimpleLexer = self.simple_t_lexer(r'expr')
        lexer = SimpleLexer('', error_class=MyLexerError)
        self.assertEqual(lexer.offset, 0)
        self.assertEqual(lexer.parent_lexer, None)
        self.assertEqual(lexer.error_class, MyLexerError)

    def test_lexer_simple_emission(self):
        SimpleLexer = self.simple_t_lexer(r'a')
        self.assertCountEqual([], SimpleLexer(''))
        self.assertCountEqual(map(Token, 'tttt', 'aaaa'), SimpleLexer('aaaa'))
        self.assertRaises(LexerError, list, SimpleLexer('aba'))

    def test_lexer_sub_lexer_emission(self):
        SimpleLexer = self.simple_t_sub_lexer(r'"', r'[a-z]', r'"')
        self.assertCountEqual(map(Token, 'tttt', 'abcd'), SimpleLexer('"abcd"'))

    def test_lexer_skip(self):
        SimpleLexer = self.simple_t_lexer(r'a|b', skip='b')
        self.assertCountEqual(map(Token, 'tt', 'aa'), SimpleLexer('abba'))

    def test_lexer_custom_name(self):
        SimpleLexer = self.simple_t_lexer(r'a', custom_name='custom')
        self.assertCountEqual([Token('custom', 'a')], SimpleLexer('a'))

if __name__ == '__main__':
    unittest.main()
