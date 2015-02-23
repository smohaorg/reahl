# Copyright 2013, 2014 Reahl Software Services (Pty) Ltd. All rights reserved.
#
#    This file is part of Reahl.
#
#    Reahl is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation; version 3 of the License.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.


# memoized
# Adapted from the original:
# http://code.activestate.com/recipes/577452/ (r1)
# Original Copyright notice:
# The MIT License (MIT)
#
# Copyright (c) 2010 Daniel Miller
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

 
from __future__ import print_function, unicode_literals, absolute_import, division

from functools import partial, wraps
import inspect
import warnings

import wrapt

@wrapt.decorator
def memoized(wrapped, instance, args, kwargs):
    if instance is None:
        return wrapped(*args, **kwargs)

    try:
        cache = instance.__cache__
    except AttributeError:
        cache = instance.__cache__ = {}

    key = (wrapped, args[1:], frozenset(kwargs.items()))
    try:
        res = cache[key]
    except KeyError:
        res = cache[key] = wrapped(*args, **kwargs)
    return res
        

def deprecated(message):
    def catch_wrapped(f):
        def is_init_or_classmethod(member):
            if inspect.ismethod(member) and member.__self__ is f:
                return True
            return (inspect.ismethod(member) or inspect.isfunction(member)) and member.__name__ == '__init__'

        @wrapt.decorator
        def deprecated_wrapper(wrapped, instance, args, kwargs):
            deprecated_thing = wrapped.__self__ if is_init_or_classmethod(wrapped) else wrapped
            warnings.warn('DEPRECATED: %s. %s' % (deprecated_thing, message), DeprecationWarning, stacklevel=2)
            return wrapped(*args, **kwargs)

        if inspect.isclass(f):
            for name, method in inspect.getmembers(f, predicate=is_init_or_classmethod):
                setattr(f, name, deprecated_wrapper(method))
            return f
        else:
            return deprecated_wrapper(f)

    return catch_wrapped


