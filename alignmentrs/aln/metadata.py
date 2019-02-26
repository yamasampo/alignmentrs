from alignmentrs.util import add_to_history


class MetadataRedirect:
    def __init__(self, instance):
        self._instance = instance
        self._axis = 0

    @property
    def rows(self):
        """pandas.core.frame.DataFrame: Returns the associated row
        metadata as a pandas DataFrame."""
        return self._instance._row_metadata

    @property
    def cols(self):
        """pandas.core.frame.DataFrame: Returns the associated column
        metadata as a pandas DataFrame."""
        return self._instance._column_metadata

    @property
    def comments(self):
        """dict: Returns the comments for this alignment."""
        return self._instance._comments

    def add_metadata(self, name, data, where, **kwargs):
        if where in ['row', 'rows']:
            self.add_row_metadata(name, data, _record_history=False, 
                                  **kwargs)
        elif where in ['col', 'cols']:
            self.add_col_metadata(name, data, _record_history=False, 
                                  **kwargs)
        elif where in ['comment', 'comments']:
            self.add_comment(name, data, _record_history=False, 
                             **kwargs)
        else:
            raise ValueError('where must be \'row\', \'col\', or \'comment\'')
        # Add to history
        add_to_history(
            self._instance, '.metadata.add_metadata',
            name, data, where
            **kwargs
        )

    def add_comment(self, name, comment, **kwargs):
        if not isinstance(name, str):
            raise ValueError('name must be str')
        elif name in self._instance._comments.keys():
            raise ValueError('name already exists')
        self._instance._comments[name] = str(comment)
        # Add to history
        add_to_history(
            self._instance, '.metadata.add_comment',
            name, comment,
            **kwargs
        )

    def add_row_metadata(self, name, data, **kwargs):
        """Adds a new column to the row metadata DataFrame.
        The resulting row metadata DataFrame is extended by one column.
        
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
        if name in self._instance._row_metadata:
            raise ValueError('name already exists')
        self._instance._row_metadata[name] = data
        # Add to history
        add_to_history(
            self._instance, '.metadata.add_row_metadata',
            name, data,
            **kwargs
        )

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
        if name in self._instance._column_metadata:
            raise ValueError('name already exists')
        self._instance._column_metadata[name] = data
        # Add to history
        add_to_history(
            self._instance, '.metadata.add_column_metadata',
            name, data,
            **kwargs
        )

    def remove_comment(self, name, **kwargs):
        if not isinstance(name, str):
            raise ValueError('name must be str')
        del self._instance._comments[name]
        # Add to history
        add_to_history(
            self._instance, '.metadata.remove_comment',
            name,
            **kwargs
        )

    def remove_row_metadata(self, name, **kwargs):
        """Removes a column from the row metadata DataFrame.
        
        Parameters
        ----------
        name : str
            Label of column to remove.
        
        """
        self._instance._row_metadata.drop(name, axis=1, inplace=True, _record_history=False)
        # Add to history
        add_to_history(
            self._instance, '.metadata.remove_row_metadata',
            name,
            **kwargs
        )

    def remove_column_metadata(self, name, **kwargs):
        """Removes a column from the column metadata DataFrame.
        
        Parameters
        ----------
        name : str
            Label of column to remove.
        
        """
        self._instance._column_metadata.drop(name, axis=1, inplace=True, _record_history=False)
        # Add to history
        add_to_history(
            self._instance, '.metadata.remove_column_metadata',
            name,
            **kwargs
        )

    def __repr__(self):
        # Returns the stringed representation of the alignment.
        parts = []
        parts.append('[Alignment.Metadata]')
        parts.append('comment_keys = [{}]'.format(
            ', '.join(list(self._instance._comments.keys()))
        ))
        parts.append('row_metadata_keys = [{}]'.format(
            ', '.join(list(self._instance._row_metadata.keys()))
        ))
        parts.append('column_metadata_keys = [{}]'.format(
            ', '.join(list(self._instance._column_metadata.keys()))
        ))
        return '\n'.join(parts)

    # TODO: Add some kind of str representation for print
    # def __str__(self):
    #     pass
