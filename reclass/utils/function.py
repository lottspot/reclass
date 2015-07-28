#
# -*- coding: utf-8 -*-
#
# This file is part of reclass (http://github.com/madduck/reclass)
#
# Copyright © 2007–14 martin f. krafft <madduck@madduck.net>
# Released under the terms of the Artistic Licence 2.0
#

from reclass.errors import UndefinedFunctionError


def get_function(name):
    if name == 'print':
        return FunctionPrint()
    if name == 'aggregate':
        return FunctionAggregate()
    else:
        raise UndefinedFunctionError(name)


class Function(object):
    def __init__(self):
        pass

    def execute(self, *args, **kwargs):
        pass


class FunctionPrint(Function):
    def __init__(self):
        super(FunctionPrint, self).__init__()

    def execute(self, additional_info, *args):
        return " ".join(args)


class FunctionAggregate(Function):
    def __init__(self):
        super(FunctionAggregate, self).__init__()

    def execute(self, additional_info, *args):
        func_filter, func_extract = args[0:2]
        hosts = additional_info
        result = {}
        matching_hosts = {}
        for hostname, hostinfo in additional_info.items():
            hostinfo = hostinfo._base
            expr = func_filter.replace("node", "hostinfo")
            if eval(expr):
                matching_hosts.update({hostname: hostinfo})
            for hostname, hostinfo in matching_hosts.items():
                expr = func_extract.replace("node", "hostinfo")
                result[hostname] = eval(expr)
        return result
