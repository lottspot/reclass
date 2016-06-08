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
    if name == 'get':
        return FunctionGet()
    if name == 'list':
        return FunctionList()
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

    def execute(self, inventory, *args):
        return " ".join(args)


class FunctionAggregate(Function):
    def __init__(self):
        super(FunctionAggregate, self).__init__()

    def execute(self, inventory, *args):
        func_filter, func_extract = args[0:2]
        result = {}
        matching_hosts = {}
        for hostname, hostinfo in inventory.items():
            node = hostinfo.parameters.as_dict()
            try:
                if eval(func_filter):
                    matching_hosts.update({hostname: node})
                for hostname, hostinfo in matching_hosts.items():
                    expr = func_extract.replace("node", "hostinfo")
                    result[hostname] = eval(expr)
            except KeyError:
                raise
        return result

class FunctionGet(Function):
    def __init__(self):
        super(FunctionGet, self).__init__()

    def execute(self, inventory, *args):
        nodename, func_extract = args[0:2]
        node = inventory[nodename].parameters.as_dict()
        return eval(func_extract)

class FunctionList(Function):
    def __init__(self):
        super(FunctionList, self).__init__()

    def execute(self, inventory, *args):
        func_filter, func_extract = args[0:2]
        result = []
        for hostname, hostinfo in inventory.items():
            node = hostinfo.parameters.as_dict()
            if eval(func_filter):
                result.append(eval(func_extract))
        return result
