"""Provides a friendly interface to the C Mud library."""

import os

from mudpy import cmud


class MudFile:
    """Provides access to data in a mud file.
    """

    def __init__(self, file, mode='r'):
        """Creates a MudFile object for interacting with mud files.

        Use with in a `with` statement to properly dispose of resources.

        :param file: Path to mud file
        :param mode: Mode for opening file
        """
        self.__cmud_file_handle = None
        self.__file_path = file
        self.__file_mode = mode.lower()

        if not os.path.exists(self.__file_path):
            raise FileNotFoundError(f"File {self.__file_path} does not exist.")

    def __enter__(self):
        if self.__file_mode == 'r':
            self.__cmud_file_handle, _ = cmud.open_read(self.__file_path)
        else:
            raise NotImplementedError(f"Open mode '{self.__file_mode}' is not implemented. "
                                      f"Only read ('r') is currently supported.")

    def __exit__(self, exc_type, exc_val, exc_tb):
        cmud.close_read(self.__cmud_file_handle)
