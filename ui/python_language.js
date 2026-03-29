


export const pythonLanguage = {
  defaultToken: '',
  tokenPostfix: '.python',
  ignoreCase: true,


  keywords: [
    'and', 'as', 'assert', 'async', 'await', 'break', 'class', 'continue',
    'def', 'del', 'elif', 'else', 'except', 'finally', 'for', 'from',
    'global', 'if', 'import', 'in', 'is', 'lambda', 'nonlocal', 'not',
    'or', 'pass', 'raise', 'return', 'try', 'while', 'with', 'yield'
  ],


  builtinTypes: [
    'int', 'float', 'str', 'bool', 'list', 'tuple', 'dict', 'set',
    'frozenset', 'bytes', 'bytearray', 'complex', 'range', 'slice',
    'type', 'object', 'None', 'NoneType', 'Any', 'Optional', 'Union',
    'List', 'Dict', 'Tuple', 'Set', 'FrozenSet', 'Type', 'Callable',
    'Iterable', 'Iterator', 'Generator', 'Sequence', 'Mapping',
    'MutableMapping', 'MutableSequence', 'AbstractSet', 'Counter',
    'DefaultDict', 'Deque', 'OrderedDict', 'ChainMap', 'TextIO',
    'BinaryIO', 'IO', 'Path', 'PathLike', 'Pattern', 'Match'
  ],


  builtinFunctions: [
    'abs', 'all', 'any', 'ascii', 'bin', 'breakpoint', 'callable',
    'chr', 'classmethod', 'compile', 'delattr', 'dir', 'divmod',
    'enumerate', 'eval', 'exec', 'filter', 'format', 'getattr',
    'globals', 'hasattr', 'hash', 'help', 'hex', 'id', 'input',
    'isinstance', 'issubclass', 'iter', 'len', 'locals', 'map',
    'max', 'min', 'next', 'oct', 'open', 'ord', 'pow', 'print',
    'property', 'repr', 'reversed', 'round', 'setattr', 'sorted',
    'staticmethod', 'sum', 'super', 'vars', 'zip', '__import__'
  ],


  builtinExceptions: [
    'BaseException', 'Exception', 'ArithmeticError', 'AssertionError',
    'AttributeError', 'EOFError', 'ImportError', 'IndexError',
    'KeyError', 'KeyboardInterrupt', 'MemoryError', 'NameError',
    'NotImplementedError', 'OSError', 'OverflowError', 'RecursionError',
    'ReferenceError', 'RuntimeError', 'StopIteration', 'SyntaxError',
    'SystemError', 'SystemExit', 'TypeError', 'UnboundLocalError',
    'UnicodeError', 'ValueError', 'ZeroDivisionError', 'Warning'
  ],


  specialVariables: ['self', 'cls', 'args', 'kwargs'],


  constants: ['True', 'False', 'None', 'NotImplemented', 'Ellipsis'],


  operators: [
    '=', '>', '<', '!', '~', '?', ':', '==', '<=', '>=', '!=', '&&', '||',
    '++', '--', '+', '-', '*', '/', '&', '|', '^', '%', '<<', '>>', '>>>',
    '+=', '-=', '*=', '/=', '&=', '|=', '^=', '%=', '<<=', '>>=', '>>>=',
    'and', 'or', 'in', 'is', 'not'
  ],


  symbols: /[=><!~?:&|+\-*\/\^%]+/,


  escapes: /\\(?:[abfnrtv\\"']|x[0-9A-Fa-f]{1,4}|u[0-9A-Fa-f]{4}|U[0-9A-Fa-f]{8})/,


  digits: /\d+(_+\d+)*/,
  octaldigits: /[0-7]+(_+[0-7]+)*/,
  binarydigits: /[0-1]+(_+[0-1]+)*/,
  hexdigits: /[[0-9a-fA-F]+(_+[0-9a-fA-F]+)*/,


  tokenizer: {
    root: [

      [/^(\s*)([a-zA-Z_]\w*)(\s*)(:)(\s*)([a-zA-Z_]\w*)/, [
        '', 'identifier', '', 'delimiter', '', 'type.identifier'
      ]],


      [/^(\s*)(class)(\s+)([a-zA-Z_]\w*)/, [
        '', 'keyword', '', 'type.identifier'
      ]],


      [/^(\s*)(async\s+)?(def)(\s+)([a-zA-Z_]\w*)(\s*)(\()/, [
        '', 'keyword', 'keyword', '', 'function', '', 'delimiter'
      ]],


      [/[a-zA-Z_]\w*/, {
        cases: {
          '@keywords': 'keyword',
          '@constants': 'constant',
          '@builtinTypes': 'type.identifier',
          '@builtinFunctions': 'function.call',
          '@builtinExceptions': 'exception',
          '@specialVariables': 'variable.language',
          '@default': 'identifier'
        }
      }],


      { include: '@whitespace' },


      [/"""|'''/, { token: 'string.delimiter', next: '@string.$0' }],


      [/f"""|f'''/, { token: 'string.delimiter', next: '@fstring.$0' }],


      [/"/, { token: 'string.delimiter', next: '@string."' }],


      [/'/, { token: 'string.delimiter', next: "@string.'" }],


      [/f"/, { token: 'string.delimiter', next: '@fstring."' }],


      [/f'/, { token: 'string.delimiter', next: "@fstring.'" }],


      [/r"""|r'''/, { token: 'string.delimiter', next: '@rstring.$0' }],
      [/r"/, { token: 'string.delimiter', next: '@rstring."' }],
      [/r'/, { token: 'string.delimiter', next: "@rstring.'" }],


      [/\d+[jJ]/, 'number.imaginary'],
      [/\d+\.\d*([eE][+-]?\d+)?[jJ]?/, 'number.float'],
      [/0[xX][0-9a-fA-F]+/, 'number.hex'],
      [/0[oO][0-7]+/, 'number.octal'],
      [/0[bB][01]+/, 'number.binary'],
      [/\d+[lL]?/, 'number'],


      [/[{}()\[\]]/, '@brackets'],
      [/[<>](?!@symbols)/, '@brackets'],
      [/@symbols/, {
        cases: {
          '@operators': 'operator',
          '@default': ''
        }
      }],


      [/#.*$/, 'comment'],
    ],

    whitespace: [
      [/[ \t\r\n]+/, 'white'],
    ],

    string: [
      [/[^"\\']+/, 'string'],
      [/\\./, 'string.escape'],
      [/("""|'''|["'])/, {
        cases: {
          '$1==@$S2': { token: 'string.delimiter', next: '@pop' },
          '@default': 'string'
        }
      }],
    ],

    fstring: [
      [/\{[^}]*\}/, 'string.escape'],
      [/[^"\\'{]+/, 'string'],
      [/\\./, 'string.escape'],
      [/("""|'''|["'])/, {
        cases: {
          '$1==@$S2': { token: 'string.delimiter', next: '@pop' },
          '@default': 'string'
        }
      }],
    ],

    rstring: [
      [/[^"\\']+/, 'string'],
      [/"""/, {
        cases: {
          '$S2=="""': { token: 'string.delimiter', next: '@pop' },
          '@default': 'string'
        }
      }],
      [/'''/, {
        cases: {
          '$S2==\'\'\'': { token: 'string.delimiter', next: '@pop' },
          '@default': 'string'
        }
      }],
      [/["']/, {
        cases: {
          '$S2==$S2': { token: 'string.delimiter', next: '@pop' },
          '@default': 'string'
        }
      }],
    ],
  },
};
