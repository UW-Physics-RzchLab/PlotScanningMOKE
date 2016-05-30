# -*- coding: utf-8 -*-

import re
import collections
from os.path import basename

def meets_conditions(conditions_dict, gleaner, x):
    gleaned = gleaner.glean(x)
    for c, v in conditions_dict.items():
        if gleaned[c] != v:
            return False
    return True

class Transformer(object):
    """A Transformer takes some x, y data and pipelines it through
    a series of user defined transformations. The order of the 
    transformations is chosen by the user. The transformations
    are only applied to data if the data's corresponding target
    (file path) matches a regex attached to the transformation.

    Requirements for transformation function call signatures:

                f(col1, col2, ..., **kwargs)

    First the function must take n arrays of data. The value 
    of n is determined by the dimensionality of datacols when
    this class is called.

    The function MUST ALSO TAKE **KWARGS! This is because passing
    the target name to transformations functions is a supported 
    feature, so all transformation funcs will be passed at 
    least on kwarg no matter what.

    Args:
        gleaner: object that provides a glean() method. Needed if you want to
            used gleaner conditions instead of a regex for the filter parameter
            in Transformer.add()
    """

    def __init__(self, gleaner=None):
        self._transformations = {}
        self.gleaner = gleaner

    def add(self, slot, func, params={}, filter='.*'):
        """Add a transformation that data will be pipelined through.

        Args:
            slot: integer that determines the order (low to high) that 
                functions will be applied to the data
            func: function to be applied to data. See class description
                for further info.
            params: dict of kwargs that will be passed to func.
            filter: regular expression that will be used to selectively apply
                this transformation to targets based on their path.
        """
        if not isinstance(slot, int):
            msg = 'slot must be integer not {}'.format(type(slot))
            raise ValueError(msg)
        if not isinstance(func, collections.Callable):
            msg = 'func must be callable, got type {}'.format(type(func))
            raise ValueError(msg)
        if isinstance(filter, dict) and self.gleaner is None:
            raise ValueError('Cannot pass dict as filter unless using gleaner')
        if slot not in list(self._transformations.keys()):
            self._transformations[slot] = (func, params, filter)
        else:
            msg = "Tried to assign a second transformation to slot {}"
            raise ValueError(msg.format(slot))

    def __call__(self, datacols, target):
        """Apply the transformations to the x, y data and
        return the result
        """ 
        # Need to get the path if target is a batchplotlib3.Target,
        # otherwise it should be a string path already.
        try:
            target = target.path
        except AttributeError:
            pass
        # Sort _transformations based on slot number from low to high
        # self.log.info('Transforming '+basename(target))
        sorted_keys = sorted(self._transformations)
        funcs, params_list = [], []
        for key in sorted_keys:
            func, params, filter = self._transformations[key]
            string_match = isinstance(filter, str) and re.match(filter, target)
            dict_match = (isinstance(filter, dict) and 
                meets_conditions(filter, self.gleaner, target))
            if string_match or dict_match:
                # self.log.info('    Applying' + func.__name__)
                funcs.append(func)
                params.update(dict(target=target))
                params_list.append(params)
        # Apply the transformations in order to the data        
        return self._pipeline(datacols, params_list, funcs)

    def _pipeline(self, datacols, params_list, funcs):
        """Take xy data and apply each func in funcs to the data
        in order."""
        for func, params in zip(funcs, params_list):
            datacols = func(*datacols, **params)
        return datacols

