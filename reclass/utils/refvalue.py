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
_RE_FUNC = '([^(]+)\((.*)\)'
_RE_FUNC = re.compile(_RE_FUNC)


class Reference(object):
    def __init__(self, string):
        self.string = string


class ReferenceFunction(Reference):
    def __init__(self, string):
        super(ReferenceFunction, self).__init__(string)

    def resolve(self, inventory, *args, **kwargs):
        return self._execute(inventory)

    def _execute(self, inventory):
        match = _RE_FUNC.match(self.string)
        func_name = match.group(1)
        func_args = match.groups()[1].split(',')

        func_args = [f.strip(' ') for f in func_args]

        try:
            func = get_function(func_name)
            ret = func.execute(inventory, *func_args)
            return ret
        except UndefinedFunctionError:
            raise UndefinedFunctionError(self.string)


class ReferenceParameter(Reference):
    def __init__(self, string):
        super(ReferenceParameter, self).__init__(string)

    def resolve(self, context, *args, **kwargs):
        path = DictPath(kwargs['delim'], self.string)
        try:
            return path.get_value(context)
        except KeyError as e:
            raise UndefinedVariableError(self.string)


class ReferenceString(object):
    def __init__(self, string):
        self._strings = []
        self._refs = []
        self._parse(string)

    def has_references(self):
        return len(self._refs) > 0

    def get_references(self):
        return self._refs

    def render(self, inventory):
        pass

    def _check_strings(self, orig, strings, sentinel):
        for s in strings:
            pos = s.find(sentinel[0])
            if pos >= 0:
                raise IncompleteInterpolationError(orig, sentinel[1])

    def _assemble(self, resolver):
        if not self.has_references():
            return self._strings[0]

        if self._strings == ['', '']:
            # preserve the type of the referenced variable
            ret = resolver(self._refs[0])
        else:

            # reassemble the string by taking a string and str(ref) pairwise
            ret = ''
            for i in range(0, len(self._refs)):
                ret += self._strings[i] + str(resolver(self._refs[i]))
            if len(self._strings) > len(self._refs):
                # and finally append a trailing string, if any
                ret += self._strings[-1]
        return ret


class ReferenceStringFunction(ReferenceString):

    INTERPOLATION_RE_FUNCTIONS = re.compile(_RE_FUNCTIONS)

    def __init__(self, string):
        super(ReferenceStringFunction,self).__init__(string)

    def _parse(self, string):
        strings, refs = self._parse_functions(string)
        self._strings = strings
        self._refs = [ReferenceFunction(ref) for ref in refs]

    def _parse_functions(self, string):
        parts = self.INTERPOLATION_RE_FUNCTIONS.split(string)
        strings = parts[0:][::2]
        functions = parts[1:][::2]
        self._check_strings(string, strings, FUNCTION_INTERPOLATION_SENTINELS)
        return (strings, functions)


    def _resolve(self, ref, inventory):
        return ref.resolve(inventory)

    def render(self, inventory):
        resolver = lambda s: self._resolve(s, inventory)
        ret = self._assemble(resolver)
        return ret


class ReferenceStringParameter(ReferenceString):
    '''
    Isolates references in string values

    ReferenceStringParameter can be used to isolate and eventually expand references to other
    parameters in strings. Those references can then be iterated and rendered
    in the context of a dictionary to resolve those references.

    ReferenceStringParameter always gets constructed from a string, because templating
    — essentially this is what's going on — is necessarily always about
    strings. Therefore, generally, the rendered value of a ReferenceStringParameter instance
    will also be a string.

    Nevertheless, as this might not be desirable, ReferenceStringParameter will return the
    referenced variable without casting it to a string, if the templated
    string contains nothing but the reference itself.

    For instance:

      mydict = {'favcolour': 'yellow', 'answer': 42, 'list': [1,2,3]}
      ReferenceStringParameter('My favourite colour is ${favolour}').render(mydict)
      → 'My favourite colour is yellow'      # a string

      ReferenceStringParameter('The answer is ${answer}').render(mydict)
      → 'The answer is 42'                   # a string

      ReferenceStringParameter('${answer}').render(mydict)
      → 42                                   # an int

      ReferenceStringParameter('${list}').render(mydict)
      → [1,2,3]                              # an list

    The markers used to identify references are set in reclass.defaults, as is
    the default delimiter.
    '''

    INTERPOLATION_RE_PARAMETER = re.compile(_RE_PARAMETER)

    def __init__(self, string, delim=PARAMETER_INTERPOLATION_DELIMITER):
        self._delim = delim
        super(ReferenceStringParameter,self).__init__(string)


    def _parse(self, string):
        parts = ReferenceStringParameter.INTERPOLATION_RE_PARAMETER.split(string)
        self._refs = parts[1:][::2]
        self._refs = [ReferenceParameter(ref) for ref in self._refs]
        self._strings = parts[0:][::2]
        self._check_strings(string, self._strings, PARAMETER_INTERPOLATION_SENTINELS)


    def _resolve(self, ref, context, additional_info):
        return ref.resolve(context, additional_info, delim=self._delim)

    def render(self, context, additional_info=None):
        resolver = lambda s: self._resolve(s, context, additional_info)
        ret = self._assemble(resolver)
        return ret

    def __repr__(self):
        do_not_resolve = lambda s: s.string.join(PARAMETER_INTERPOLATION_SENTINELS)
        return 'ReferenceStringParameter(%r, %r)' % (self._assemble(do_not_resolve),
                                     self._delim)
