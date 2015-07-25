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

    def execute(self, *args):
        return " ".join(*args)


class FunctionAggregate(Function):
    def __init__(self):
        super(FunctionAggregate, self).__init__()

    def execute(self, *args):
        return "{aggregate()}"
        #result = []
        #matching_hosts = []
        #for host in hosts:
        #    if func_args[0](host) is True:
        #        matching_hosts.append(host)
        #result = []
        #for host in matching_hosts:
        #    result.append(func_args[1](host))
        #return result


