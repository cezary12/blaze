from __future__ import absolute_import, division, print_function

import os

import datashape

from .data_descriptor import IDataDescriptor
from .. import py2help
from dynd import nd
from .dynd_data_descriptor import DyNDDataDescriptor, Capabilities


def json_descriptor_iter(array):
    for row in array:
        yield DyNDDataDescriptor(row)


class JSONDataDescriptor(IDataDescriptor):
    """
    A Blaze data descriptor which exposes a JSON file.

    Parameters
    ----------
    filename : string
        A path string for the JSON file.
    schema : string or blaze.datashape
        A blaze datashape (or its string representation) of the schema
        in the JSON file.
    """
    def __init__(self, filename, **kwargs):
        if os.path.isfile(filename) is not True:
            raise ValueError('JSON file "%s" does not exist' % filename)
        self.filename = filename
        schema = kwargs.get("schema", None)
        if type(schema) in py2help._strtypes:
            schema = datashape.dshape(schema)
        self.schema = str(schema)
        # Initially the array is not loaded (is this necessary?)
        self._cache_arr = None

    @property
    def dshape(self):
        return datashape.dshape(self.schema)

    @property
    def capabilities(self):
        """The capabilities for the json data descriptor."""
        return Capabilities(
            # json datadescriptor cannot be updated
            immutable = False,
            # json datadescriptors are concrete
            deferred = False,
            # json datadescriptor is persistent
            persistent = True,
            # json datadescriptor can be appended efficiently
            appendable = True,
            remote = False,
            )

    @property
    def _arr_cache(self):
        if self._cache_arr is not None:
            return self._cache_arr
        with open(self.filename) as jsonfile:
            # This will read everything in-memory (but a memmap approach
            # is in the works)
            self._cache_arr = nd.parse_json(
                self.schema, jsonfile.read())
        return self._cache_arr

    def dynd_arr(self):
        return self._arr_cache

    def __array__(self):
        return nd.as_numpy(self.dynd_arr())

    def __len__(self):
        # Not clear to me what the length of a json object should be
        return None

    def __getitem__(self, key):
        return DyNDDataDescriptor(self._arr_cache[key])

    def __setitem__(self, key, value):
        # JSON files cannot be updated (at least, not efficiently)
        raise NotImplementedError

    def __iter__(self):
        return json_descriptor_iter(self._arr_cache)
