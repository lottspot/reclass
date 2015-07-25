#
# -*- coding: utf-8 -*-
#
# This file is part of reclass (http://github.com/madduck/reclass)
#
# Copyright © 2007–14 martin f. krafft <madduck@madduck.net>
# Released under the terms of the Artistic Licence 2.0
#

import re

from reclass.utils.dictpath import DictPath
from reclass.defaults import PARAMETER_INTERPOLATION_SENTINELS, \
        PARAMETER_INTERPOLATION_DELIMITER, \
        FUNCTION_INTERPOLATION_SENTINELS
from reclass.errors import IncompleteInterpolationError, \
        UndefinedVariableError, \
        UndefinedFunctionError
from reclass.utils.function import get_function

_SENTINELS_PARAMETER = [re.escape(s) for s in PARAMETER_INTERPOLATION_SENTINELS]
_SENTINELS_FUNCTIONS = [re.escape(s) for s in FUNCTION_INTERPOLATION_SENTINELS]

_RE_PARAMETER = '{0}\s*(.+?)\s*{1}'.format(*_SENTINELS_PARAMETER)
_RE_FUNCTIONS = '{0}\s*(.+?)\s*{1}'.format(*_SENTINELS_FUNCTIONS)

# matches a string like 'function, args)'
_RE_FUNC = '([^(]+)\(([^)]+)\)'
_RE_FUNC = re.compile(_RE_FUNC)


class Reference(object):
    def __init__(self, string):
        self.string = string


class ReferenceFunction(Reference):
    def __init__(self, string):
        super(ReferenceFunction, self).__init__(string)

    def resolve(self, context, **kwargs):
        return self._execute(context)

    def _execute(self, context):
        match = _RE_FUNC.match(self.string)
        func_name = match.group(1)
        func_args = match.groups()[1].split(',')

        func_args = [f.strip(' ') for f in func_args]

        try:
            func = get_function(func_name)
            return func.execute(func_args)
        except UndefinedFunctionError:
            raise UndefinedFunctionError(self.string)

    def get_dependences(self, **kwargs):
        return []


class ReferenceParameter(Reference):
    def __init__(self, string):
        super(ReferenceParameter, self).__init__(string)

    def resolve(self, context, **kwargs):
        path = DictPath(kwargs['delim'], self.string)
        try:
            return path.get_value(context)
        except KeyError as e:
            raise UndefinedVariableError(self.string)

    def get_dependencies(self, **kwargs):
        return [DictPath(kwargs['delim'], self.string)]


class RefValue(object):
    '''
    Isolates references in string values

    RefValue can be used to isolate and eventually expand references to other
    parameters in strings. Those references can then be iterated and rendered
    in the context of a dictionary to resolve those references.

    RefValue always gets constructed from a string, because templating
    — essentially this is what's going on — is necessarily always about
    strings. Therefore, generally, the rendered value of a RefValue instance
    will also be a string.

    Nevertheless, as this might not be desirable, RefValue will return the
    referenced variable without casting it to a string, if the templated
    string contains nothing but the reference itself.

    For instance:

      mydict = {'favcolour': 'yellow', 'answer': 42, 'list': [1,2,3]}
      RefValue('My favourite colour is ${favolour}').render(mydict)
      → 'My favourite colour is yellow'      # a string

      RefValue('The answer is ${answer}').render(mydict)
      → 'The answer is 42'                   # a string

      RefValue('${answer}').render(mydict)
      → 42                                   # an int

      RefValue('${list}').render(mydict)
      → [1,2,3]                              # an list

    The markers used to identify references are set in reclass.defaults, as is
    the default delimiter.
    '''

    INTERPOLATION_RE_PARAMETER = re.compile(_RE_PARAMETER)
    INTERPOLATION_RE_FUNCTIONS = re.compile(_RE_FUNCTIONS)

    def __init__(self, string, delim=PARAMETER_INTERPOLATION_DELIMITER):
        self._strings = []
        self._refs = []
        self._delim = delim
        self._parse(string)

    def _parse(self, string):
        parts = RefValue.INTERPOLATION_RE_PARAMETER.split(string)
        self._refs = parts[1:][::2]
        self._refs = [ReferenceParameter(ref) for ref in self._refs]
        self._strings = parts[0:][::2]
        self._check_strings(string, self._strings, PARAMETER_INTERPOLATION_SENTINELS)

        # each string could contain a function
        for i in range(len(self._strings)):
            strings, refs = self._parse_functions(self._strings[i])
            refs = [ReferenceFunction(ref) for ref in refs]
            if len(refs) == 0:
                continue
            del self._strings[i]
            self._strings.insert(i, strings)
            self._refs.insert(i, refs)

        self._refs = self._flatten(self._refs)
        self._strings = self._flatten(self._strings)

    def _flatten(self, l):
        ret = []
        for element in l:
            if isinstance(element, list):
                ret.extend(element)
            else:
                ret.append(element)
        return ret

    def _parse_functions(self, string):
        parts = RefValue.INTERPOLATION_RE_FUNCTIONS.split(string)
        strings = parts[0:][::2]
        functions = parts[1:][::2]
        self._check_strings(string, strings, FUNCTION_INTERPOLATION_SENTINELS)
        return (strings, functions)

    def _check_strings(self, orig, strings, sentinel):
        for s in strings:
            pos = s.find(sentinel[0])
            if pos >= 0:
                raise IncompleteInterpolationError(orig, sentinel[1])

    def _resolve(self, ref, context):
        return ref.resolve(context, delim=self._delim)

    def has_references(self):
        return len(self._refs) > 0

    def get_references(self):
        return self._refs

    def _assemble(self, resolver):
        if not self.has_references():
            return self._strings[0]

        if self._strings == ['', '']:
            # preserve the type of the referenced variable
            return resolver(self._refs[0])

        # reassemble the string by taking a string and str(ref) pairwise
        ret = ''
        for i in range(0, len(self._refs)):
            ret += self._strings[i] + str(resolver(self._refs[i]))
        if len(self._strings) > len(self._refs):
            # and finally append a trailing string, if any
            ret += self._strings[-1]
        return ret

    def render(self, context):
        resolver = lambda s: self._resolve(s, context)
        ret = self._assemble(resolver)
        return ret

    def __repr__(self):
        do_not_resolve = lambda s: s.string.join(PARAMETER_INTERPOLATION_SENTINELS)
        return 'RefValue(%r, %r)' % (self._assemble(do_not_resolve),
                                     self._delim)
