from collections import Counter
from copy import deepcopy
import warnings
import os
import inspect

import pandas
import numpy

from libalignmentrs.alignment import BaseAlignment
from libalignmentrs.record import BaseRecord
from alignmentrs.util import idseq_to_display
from alignmentrs.aln.mixins import (RecordsSerdeMixin, FastaSerdeMixin,
                                    JsonSerdeMixin, PickleSerdeMixin)
from alignmentrs.history import History, Record
from .mutator import RowMutator, ColMutator


__all__ = ['Alignment', 'CatAlignment']


class NoNameWarning(UserWarning):
    """Warning for mismatched/incompatible alignments.
    """
    pass

class DuplicateNameWarning(UserWarning):
    """Warning for mismatched/incompatible alignments.
    """
    pass

class Alignment(PickleSerdeMixin, JsonSerdeMixin, FastaSerdeMixin, 
                RecordsSerdeMixin, object):
    """Reperesents a multiple sequence alignment of samples.

    The Alignment object encapsulates information generally
    included in the FASTA format:
    - sequence names/ids
    - descriptions
    - sequences

    Additionally, the Alignment object also stores comments
    (lines prefixed by a semicolon ";") as metadata.

    Attributes
    ----------
    name : str
        Name of the alignment.
    samples : BaseAlignment
        Alignment of sample sequences.
    metadata : dict
        Other information related to the alignment.
    """
    def __init__(self, name, records, chunk_size: int=1,
                 index=None, metadata: dict=None, column_metadata=None,
                 store_history=True, **kwargs):
        """Creates a new Alignment object from a sample BaseAlignment.

        Parameters
        ----------
        name : str
            Name of the alignment.
        records : list of BaseRecord
            Aligned sequences as a list of records.
        chunk_size : int, optional
            Character length of each column in the alignment.
        index : pandas.Index optional
            Index for alignment columns.
        metadata : dict, optional
            Other information related to the alignment. (default is None,
            which creates a blank dictionary)
        column_metadata : pandas.DataFrame or dict, optional
            DataFrame containing annotation for columns.
        store_history : bool, optional
            Whether or not to store actions when the state of the Alignment changes.
        metadata : dict, optional
            Other information related to the alignment. (default is None,
            which creates a blank dictionary)
        **kwargs
            Other keyword arguments used to initialize states in the
            Alignment object.

        """
        self.name = name
        self._alignment: BaseAlignment = \
            self._alignment_constructor(records, chunk_size)
        self._index = self._index_constructor(index)
        self.metadata = self._metadata_constructor(metadata)
        self._column_metadata = \
            self._col_metadata_constructor(column_metadata, self.index)
        self._rows = RowMutator(self)
        self._cols = ColMutator(self)
        # TODO: Add initial state information
        self._history = History() if store_history else None

    # Constructors
    def _alignment_constructor(self, records, chunk_size):
        # Constructs a BaseAlignemnt from the input
        # `records` can be a list of BaseRecord or a BaaseAlignment
        # Otherwise, raises a TypeError
        # TODO: Handle possibility of empty alignment
        if isinstance(records, list):
            if not sum((isinstance(rec, BaseRecord) for rec in records)):
                raise TypeError('records must be a list of BaseRecord objects')
            return BaseAlignment(records, chunk_size)
        elif isinstance(records, BaseAlignment):
            if records.chunk_size != chunk_size:
                records.chunk_size = chunk_size
            return records
        raise TypeError('records must be a list of BaseRecord objects or a BaseAlignment')

    def _metadata_constructor(self, metadata):
        # Constructs metadata dictionary
        # `metadata` can be a ditionary or None
        # TODO: Handle any kind of mapping instead of only a dictionary
        if metadata is None:
            return dict()
        elif isinstance(metadata, dict):
            return metadata
        raise TypeError('metadata must be a dictionary object')

    def _index_constructor(self, index):
        # Constructs index from input.
        # `index` can be pandas.Index, list or None.
        # Otherwise, raises an error.
        # TODO: Handle rangle, numpy array
        if index is None:
            return pandas.Index(range(self._alignment.ncols))
        elif isinstance(index, pandas.Index):
            return index
        elif isinstance(index, list):
            return pandas.Index(index)
        raise TypeError(
            'index must be a list or {} object'.format(pandas.Index.__mro__[0]))

    def _col_metadata_constructor(self, column_metadata, index):
        # Constructs column metadata DataFrame from `column_metadata` and
        # `index` inputs`.
        # `column_metadata` must be None, dict, or pandas.DataFrame
        # Otherwise raises TypeError. 
        if column_metadata is None:
            df = pandas.DataFrame(None, index=index)
        elif isinstance(column_metadata, dict):
            # Check if values match the length of the index
            for key, val in column_metadata.items():
                if len(val) != len(self.index):
                    raise ValueError('{} value length does not match the number of columns'.format(key))
            df = pandas.DataFrame(column_metadata, index=self.index)
        elif isinstance(column_metadata, pandas.DataFrame):
            if len(column_metadata) != len(self.index):
                raise ValueError('length of column_metadata dataframe does not match the number of columns'.format(key))
            column_metadata.index = self.index
            df = column_metadata
        else:
            raise TypeError('column_metadata must be a dictionary or a {} object'.format(pandas.DataFrame.__mro__[0]))
        return df

    # Properties
    @property
    def rows(self):
        # Redirects to _rows "virtual object" to access row-specific methods
        return self._rows

    @property
    def cols(self):
        # Redirects to _cols "virtual object" to access column-specific methods
        return self._cols

    @property
    def index(self):
        """pandas.core.indexes.base.Index: Returns the column index
        of the alignment."""
        return self._index

    @index.setter
    def set_index(self, index: pandas.core.indexes.base.Index):
        """Sets the column index of the alignment."""
        index = pandas.Index(index)
        self._column_metadata.index = index
        self._index = index
        # Add history by default
        if self._history is not None:
            self._history.add('.index', args=[index])

    @property
    def chunk_size(self):
        """int: Returns the chunk size of the alignment."""
        return self._alignment.chunk_size

    @chunk_size.setter
    def chunk_size_setter(self, value: int):
        """Changes the number of characters in an alignment column
        using default options.
        For more control, use the `set_chunk_size` method."""
        self.set_chunk_size(self, value, reset_index=True)
        # Add history by default
        if self._history is not None:
            self._history.add('.chunk_size', args=[value])

    @property
    def column_metadata(self):
        """pandas.core.frame.DataFrame: Returns the associated column
        metadata as a pandas DataFrame."""
        return self._column_metadata

    @property
    def nrows(self):
        """int: Returns the number of rows in the alignment."""
        return self._alignment.nrows

    @property
    def ncols(self):
        """int: Returns the number of columns in the alignment."""
        return self._alignment.ncols

    @property
    def nchars(self):
        """int: Returns the number of aligned characters
        (ncols * chunk_size)."""
        return self._alignment.nchars

    @property
    def records(self):
        """list of BaseRecord: Returns the list of records."""
        return self._alignment.records

    @property
    def ids(self):
        """list of str: Returns the list of identifiers."""
        return self._alignment.ids

    @property
    def descriptions(self):
        """list of str: Returns the list of descriptions."""
        return self._alignment.descriptions

    @property
    def sequences(self):
        """list of str: Returns the list of sequences."""
        return self._alignment.sequences

    @property
    def chunked_sequences(self):
        """list of list of str: Returns the list of sequences."""
        return self._alignment.chunked_sequences

    @property
    def history(self):
        """History: Returns history of previous actions performed that may have
        changed the state of the alignment."""
        return self._history


    # Methods
    # ==========================================================================

    def copy(self, **kwargs):
        """Creates a deep copy of the alignment.
        
        Returns
        -------
        Alignment
            The new alignment is an new independent copy.
            Changes made in the new alignment will not affect the original, and
            vice versa.

        """

        # TODO: Implement magic methods for copy and deepcopy instead
        # TODO: Copy over previous history
        record = True
        if '_record_history' in kwargs.keys():
            record = kwargs['_record_history']
            del kwargs['_record_history']
        if record and (self._history is not None):
            self._history.add('.copy')
        return self.__class__(
            self.name, self._alignment.copy(),
            chunk_size=self.chunk_size,
            index=self._index.copy(deep=True),
            metadata=deepcopy(self.metadata),
            column_metadata=self._column_metadata.copy(deep=True)
        )

    def set_chunk_size(self, value, copy=False, recasting_func=None, 
                       reset_index=False, **kwargs):
        """Changes the number of characters for each alignment column
        using default options.
        
        Parameters
        ----------
        value : int
            Number of characters.
        copy : bool, optional
            Whether or not change the chunk size in a new copy or
            perform the operation inplace. (default is False, performs the
            change inplace)
        recasting_func : function, optional
            Function used to recast existing column metadata to the
            new alignment. (default is None, the existing column metadata will be recasted using by averaging for numerical data,
            or by mode for objects)
        reset_index : bool, optional
            Must be set to True. (the default is False, in order to explicitly
            require permission)

        Returns
        -------
        Alignment or None
            If copy is True, returns a deep copy of the Alignment with the
            new chunk size. Otherwise, the operation is performed inplace and does not return any value.

        """
        if reset_index is not True:
            raise ValueError(
                'cannot change chunk size without resetting the current index')
        aln = self
        if copy is True:
            aln = self.copy()
        # Changing chunk size to invalid size will raise an error
        curr_chunk_size = aln.chunk_size
        aln._alignment.chunk_size = value

        # Adjust column metadata
        if recasting_func is None:
            # current size -> 1's -> new size
            df = self._default_expander_func(
                aln._column_metadata, curr_chunk_size)
            # print(curr_chunk_size, value, len(df))
            df = self._default_reducer_func(df, value)
            # print(curr_chunk_size, value, len(df))
        else:
            df = recasting_func(
                aln._column_metadata, curr_chunk_size, value)
        aln._column_metadata = df
        # Add to history
        record = True
        if '_record_history' in kwargs.keys():
            record = kwargs['_record_history']
            del kwargs['_record_history']
        if record and (aln._history is not None):
            aln._history.add('.set_chunk_size',
                args=[value],
                kwargs={
                    'copy': copy,
                    'recasting_func': 
                        repr(inspect.signature(recasting_func))
                            .lstrip('<Signature ').rstrip('>'),
                    'reset_index': reset_index
                })
        if copy is True:
            return aln

    def add_column_metadata(self, name, data, **kwargs):
        """Adds a new column to the column metadata DataFrame.
        The resulting column metadata DataFrame is extended by one column.
        
        Parameters
        ----------
        name : str
            Name describing the metadata
        data : list
            Data to be added
        
        Raises
        ------
        ValueError
            If the value of `name` is already one of the existing
            column labels.
        
        """
        if name in self._column_metadata:
            raise ValueError('name already exists')
        self._column_metadata[name] = data
        # Add to history
        record = True
        if '_record_history' in kwargs.keys():
            record = kwargs['_record_history']
            del kwargs['_record_history']
        if record and (self._history is not None):
            self._history.add('.set_chunk_size',
                args=[name, data])

    def remove_column_metadata(self, name, **kwargs):
        """Removes a column from the column metadata DataFrame.
        
        Parameters
        ----------
        name : str
            Label of column to remove.
        
        """
        self._column_metadata.drop(name, axis=1, inplace=True, _record_history=False)
        # Add to history
        record = True
        if '_record_history' in kwargs.keys():
            record = kwargs['_record_history']
            del kwargs['_record_history']
        if record and (self._history is not None):
            self._history.add('.remove_column_metadata',
                args=[name])

    def reset_index(self, copy=False, **kwargs):
        """Resets the alignment index.
        
        Parameters
        ----------
        copy : bool, optional
            Whether to reset the index on a copy of the alignment or
            reset the index inplace. (default is False, the index of the
            alignment is reset inplace)
        
        Returns
        -------
        Alignment or None
            If copy is True, returns a deep copy of the Alignment with the
            new index. Otherwise, the operation is performed inplace and does
            not return any value.

        """
        aln = self._instance
        if copy is True:
            aln = self._instance.copy()
        # Add to history
        record = True
        if '_record_history' in kwargs.keys():
            record = kwargs['_record_history']
            del kwargs['_record_history']
        if record and (self._history is not None):
            aln._history.add('.reset_index')
        aln.cols.reset_index(copy=False, _record_history=False)
        if copy is True:
            return aln

    def variants(self):
        """Returns a list of Counter dictionaries containg the identities and
        frequency of variants in each column of the alignment.

        This is a shortcut for using the Counter constructor on the
        `map` method for columns in the alignment.
        
        Returns
        -------
        list of Counter 

        """
        return list(self.cols.map(Counter))

    def consensus(self, threshold=0.5):
        """Returns the consensus sequence of the alignment.
        
        Parameters
        ----------
        threshold : bool, optional
            Percent threshold of rows a variant must occur in order to be
            considered the consensus sequence for the column.
            If no variant meets this threshold, `None` is used instead.
            (default is 0.5, which means variants occuring greater than
            or equal to 50% of the rows become the consensus sequence.)
        
        Returns
        -------
        list of str

        """
        cons = []
        for cnts in self.cols.map(Counter):
            char, cnt = max(cnts.items(), key=lambda x: x[1])
            if cnt < self.nrows * threshold:
                char = None
            cons.append(char)
        return cons

    def drop(self, value, case_sensitive=False, copy=False, dry_run=False, 
             mode='any', **kwargs):
        """Drops columns given a certain value.
        
        Parameters
        ----------
        value : str
            Character/s to match against.
        case_sensitive : bool, optional
            Whether of not the character search is case sensitive.
            (default is False, search is case insensitive)
        copy : bool, optional
            Whether to drop columns on a copy of the alignment or
            perform the dropping inplace. 
            (default is False, dropping is performed inplace)
        dry_run : bool, optional
            If True, shows the number of columns to be dropped (True)
            and returns the list of column positions to be dropped.
            No changes are made to the alignment at this point.
            If False, columns with the value are removed.
            (default is False, dropping is performed immediately)
        mode : str, optional
            Method used to decide when a column is dropped.
            If the value is 'any', the column will be dropped when
            at least one match is found.
            If the value if 'all', the column will be dropped only if
            the entire column matches the specified value.
            (the default is 'any', any match drops the column)
        
        Returns
        -------
        Alignment or None
            If copy is True, returns a deep copy of the Alignment after dropping
            matching columns. Otherwise, dropping is performed inplace
            and does not return any value.

        """
        # Add to history
        record = True
        if dry_run:
            record = False
        elif '_record_history' in kwargs.keys():
            record = kwargs['_record_history']
            del kwargs['_record_history']
        if record and (self._history is not None):
            self._history.add('.drop',
                args=[value],
                kwargs={
                    'case_sensitive': case_sensitive,
                    'copy': copy,
                    'dry_run': dry_run,
                })
        return self.cols.drop(value, case_sensitive=case_sensitive,
                              copy=copy, dry_run=dry_run, mode=mode,
                              _record_history=False)

    def drop_except(self, value, case_sensitive=False, copy=False,
                    dry_run=False, mode='any', **kwargs):
        """Drops columns given a certain value.
        
        Parameters
        ----------
        value : str
            Character/s to match against.
        case_sensitive : bool, optional
            Whether of not the character search is case sensitive.
            (default is False, search is case insensitive)
        copy : bool, optional
            Whether to drop columns on a copy of the alignment or
            perform the dropping inplace. 
            (default is False, dropping is performed inplace)
        dry_run : bool, optional
            If True, shows the number of columns to be kept (True)
            and returns the list of column positions to be kept.
            No changes are made to the alignment at this point.
            If False, columns matching the value are kept.
            (default is False, dropping is performed immediately)
        mode : str, optional
            Method used to decide when a column is dropped.
            If the value is 'any', the column will be kept when
            at least one match is found.
            If the value if 'all', the column will be kept only if
            the entire column matches the specified value.
            (the default is 'any', any match drops the column)
        
        Returns
        -------
        Alignment or None
            If copy is True, returns a deep copy of the Alignment after dropping
            columns that did not match the value. Otherwise, dropping is
            performed inplace and does not return any value.

        """
        # Add to history
        record = True
        if dry_run:
            record = False
        elif '_record_history' in kwargs.keys():
            record = kwargs['_record_history']
            del kwargs['_record_history']
        if record and (self._history is not None):
            self._history.add('.drop_except',
                args=[value],
                kwargs={
                    'case_sensitive': case_sensitive,
                    'copy': copy,
                    'dry_run': dry_run,
                    'mode': mode,
                })
        return self.cols.drop_except(value, case_sensitive=case_sensitive,
                                     copy=copy, dry_run=dry_run, mode=mode,
                                     _record_history=False)

    def drop_n(self, n_char='N', case_sensitive=False, copy=False,
               dry_run=False, **kwargs):
        """Drops columns that has the 'N' ambiguity character.
        
        Parameters
        ----------
        n_char : str, optional
            Ambiguity character to match against.
            (default is 'N')
        case_sensitive : bool, optional
            Whether of not the character search is case sensitive.
            (default is False, search is case insensitive)
        copy : bool, optional
            Whether to drop columns on a copy of the alignment or
            perform the dropping inplace. 
            (default is False, dropping is performed inplace)
        dry_run : bool, optional
            If True, shows the number of columns to be dropped (True)
            and returns the list of column positions to be dropped.
            No changes are made to the alignment at this point.
            If False, columns with the value are removed.
            (default is False, dropping is performed immediately)
        mode : str, optional
            Method used to decide when a column is dropped.
            If the value is 'any', the column will be dropped when
            at least one match is found.
            If the value if 'all', the column will be dropped only if
            the entire column matches the specified value.
            (the default is 'any', any match drops the column)
        
        Returns
        -------
        Alignment or None
            If copy is True, returns a deep copy of the Alignment after dropping
            columns with the ambiguity character. Otherwise, dropping is
            performed inplace and does not return any value.

        """
        # Add to history
        record = True
        if dry_run:
            record = False
        elif '_record_history' in kwargs.keys():
            record = kwargs['_record_history']
            del kwargs['_record_history']
        if record and (self._history is not None):
            self._history.add('.drop_n',
                kwargs={
                    'n_char': n_char,
                    'case_sensitive': case_sensitive,
                    'copy': copy,
                    'dry_run': dry_run,
                })
        return self.cols.drop_n(n_char=n_char, case_sensitive=case_sensitive,
                                copy=copy, dry_run=dry_run, _record_history=False)

    def drop_gap(self, gap_char='-', copy=False, dry_run=False, **kwargs):
        """Drops columns that has the '-' gap character.
        
        Parameters
        ----------
        n_char : str, optional
            Gap character to match against. (default is '-')
        case_sensitive : bool, optional
            Whether of not the character search is case sensitive.
            (default is False, search is case insensitive)
        copy : bool, optional
            Whether to drop columns on a copy of the alignment or
            perform the dropping inplace. 
            (default is False, dropping is performed inplace)
        dry_run : bool, optional
            If True, shows the number of columns to be dropped (True)
            and returns the list of column positions to be dropped.
            No changes are made to the alignment at this point.
            If False, columns with the value are removed.
            (default is False, dropping is performed immediately)
        mode : str, optional
            Method used to decide when a column is dropped.
            If the value is 'any', the column will be dropped when
            at least one match is found.
            If the value if 'all', the column will be dropped only if
            the entire column matches the specified value.
            (the default is 'any', any match drops the column)
        
        Returns
        -------
        Alignment or None
            If copy is True, returns a deep copy of the Alignment after dropping
            columns with the gap character. Otherwise, dropping is
            performed inplace and does not return any value.

        """
        # Add to history
        record = True
        if dry_run:
            record = False
        elif '_record_history' in kwargs.keys():
            record = kwargs['_record_history']
            del kwargs['_record_history']
        if record and (self._history is not None):
            self._history.add('.drop_gap',
                kwargs={
                    'gap_char': gap_char,
                    'copy': copy,
                    'dry_run': dry_run,
                })
        return self.cols.drop_gap(gap_char=gap_char, copy=copy, 
                                  dry_run=dry_run, _record_history=False)

    def join(self, others, reset_index=False, copy=False, **kwargs):
        """Marges the current alignment with one or more other alignments.
        This extends the number of columns in the alignment.
        
        Parameters
        ----------
        others : Alignment or list of Alignment
            Other alignments to append to the current alignment.
        reset_index : bool, optional
            Whether to reset the index on a copy of the alignment or
            reset the index inplace. (default is False, the index of the
            alignment is reset inplace)
        copy : bool, optional
            Whether to keep the current alignment intact and create a new copy of the joined alignment or join the alignments inplace.
            (default is False, joining is performed inplace)
        
        Returns
        -------
        Alignment or None
            If copy is True, returns a deep copy of the Alignment after joining with the other alignment/s. Otherwise, dropping is
            performed inplace and does not return any value.

        """
        aln = self
        if copy is True:
            aln = self.copy()
        if isinstance(others, Alignment):
            balns = [others._alignment]
            others = [others]
        elif isinstance(others, list) and \
            sum((isinstance(o, Alignment) for o in others)) == len(others):
            balns = [o._alignment for o in others]
        else:
            raise ValueError(
                'others must be an Alignment or ''a list of Alignment objects')
        # check if chunks are the same
        # check if number of records are the same
        curr_ncols = aln.ncols
        aln._alignment.concat(balns)
        # Concat dataframes
        aln._column_metadata = pandas.concat(
            [aln._column_metadata] + 
            [aln._column_metadata for aln in others],
            sort=False, axis=0
        )
        # Add names
        name_list = ([aln.name]*curr_ncols) + \
                    [o.name for o in others for _ in range(o.ncols)]
        if None in name_list:
            warnings.warn('used `None` in _src_name column metadata '
                'because some alignments have no name', NoNameWarning)
        if set(name_list) != len(others) + 1:
            warnings.warn('some alignments have the same name', 
                DuplicateNameWarning)
        aln._column_metadata['_src_name'] = name_list
        # Concat index
        if reset_index is True:
            aln._index = pandas.Index(range(
                sum([len(aln._index)] + [len(o._index) for o in others])
            ))
            aln._column_metadata.reset_index(drop=True, inplace=True)
        else:
            aln._index = pandas.Index(pandas.concat(
                [pandas.Series(aln._index)] + 
                [pandas.Series(o._index) for o in others]
            ))
        # Add to history
        record = True
        if '_record_history' in kwargs.keys():
            record = kwargs['_record_history']
            del kwargs['_record_history']
        if record and (aln._history is not None):
            aln._history.add('.join',
                args=[others],
                kwargs={
                    'reset_index': reset_index,
                    'copy': copy,
                })
        if copy is True:
            return aln

    @staticmethod
    def _default_expander_func(df, n):
        return pandas.DataFrame(
                {col: numpy.repeat(df.values, n) for col in df})

    @staticmethod
    def _default_reducer_func(df, n):
        def apply_func(x, col):
            if x[col].dtype != numpy.dtype('O'):
                return max(Counter(x[col]).items(), key=lambda y: y[1])[0]
            return numpy.mean(x[col])
        grouper = numpy.arange(len(df))//n
        return df.groupby(grouper) \
                 .apply(lambda x: pandas.Series(
                    {col: apply_func(x, col) for col in df}))

    # TODO: implement __copy__ and __deepcopy__

    # Special methods
    # ==========================================================================

    def __getitem__(self, key):
        if isinstance(key, str):
            return self.rows.__getitem__(key)
        elif isinstance(key, list) and \
            sum((isinstance(val, str) for val in key)):
            return self.rows.__getitem__(key)
        elif isinstance(key, int) or isinstance(key, slice):
            return self.cols.__getitem__(key)
        elif isinstance(key, list) and \
            sum((isinstance(val, int) for val in key)):
            return self.cols.__getitem__(key)
        raise TypeError('key must be str or int')

    # def __delitem__(self, key):
    #     if isinstance(key, str):
    #         if key in self.ids:
    #             i = self._alignment.row_names_to_indices([key])
    #             return self._alignment.remove_records(i)
    #         raise KeyError('key did not match any identifier')
    #     elif isinstance(key, int):
    #         return self.remove_cols(key)
    #     raise TypeError('key must be str or int')

    def __iter__(self):
        raise NotImplementedError(
            'Use .rows.iter() or .rows.iter_sequences() '
            'to iterate over records or sample sequences, respectively.\n'
            'Use .cols.iter() to iterate across columns in the alignment.')

    def __repr__(self):
        parts = []
        parts.append('[Alignment]')
        parts.append('name = {}'.format(self.name))
        parts.append('nrows = {}'.format(self.nrows))
        parts.append('ncols = {}'.format(self.ncols))
        parts.append('chunk_size = {}'.format(self.chunk_size))
        if self:
            aln = idseq_to_display(self.ids, self.chunked_sequences)
            parts += ['', aln, '']
        parts.append('metadata_keys = [{}]'.format(
            ', '.join(list(self.metadata.keys()))
        ))
        parts.append('column_metadata_keys = [{}]'.format(
            ', '.join(list(self._column_metadata.keys()))
        ))
        return '\n'.join(parts)

    def __str__(self):
        return str(self._alignment)

    def __len__(self):
        raise NotImplementedError(
            'Use .nrows to get the number of samples, or '
            '.ncols to get the number of columns in the alignment.')

    def __bool__(self):
        if self.ncols == 0 or self.nrows == 0:
            return False
        return True

    def __hash__(self):
        return hash(self.to_dict(column_metadata=True).items())

    def __eq__(self, other):
        return hash(self) == hash(other)
