"""Provides a friendly interface to the C Mud library."""

import os
import logging

from mudpy import cmud


class Histogram:
    def __init__(self):
        raise NotImplementedError()

    def get_hist_t0_ps(self):
        raise NotImplementedError()

    def get_hist_good_bin_one(self):
        raise NotImplementedError()

    def get_hist_good_bin_two(self):
        raise NotImplementedError()

    def get_hist_background_one(self):
        raise NotImplementedError()

    def get_hist_background_two(self):
        raise NotImplementedError()

    def get_hist_num_events(self):
        raise NotImplementedError()

    def get_hist_title(self):
        raise NotImplementedError()


class HistogramCollection:
    def __init__(self):
        raise NotImplementedError()

    def __getitem__(self, item):
        raise NotImplementedError()

    def get_hist_type(self):
        raise NotImplementedError()

    def get_hist_num_bytes(self):
        raise NotImplementedError()

    def get_hist_num_bins(self):
        raise NotImplementedError()

    def get_hist_bytes_per_bin(self):
        raise NotImplementedError()

    def get_hist_fs_per_bin(self):
        raise NotImplementedError()

    def get_hist_seconds_per_bin(self):
        raise NotImplementedError()


class MudFile:
    """Provides access to data in a mud file.
    """

    def __init__(self, file: str, mode: str = 'r', default_string_buffer_size: int = 256):
        """Creates a MudFile object for interacting with mud files.

        Use with in a `with` statement to properly dispose of resources. Won't through an exception for improper files
        until you attempt to get data.

        :param file: Path to mud file
        :param mode: Mode for opening file
        :param default_string_buffer_size: The default buffer size to use when retrieving string values
        :raises FileNotFoundError: File does not exist. Does not raise an error if the file is not correctly formatted.
        """
        self.__logger = logging.getLogger(__name__)
        self.__cmud_file_handle = None
        self.__file_path = file
        self.__file_mode = mode.lower()
        self.__default_string_buffer_size = int(default_string_buffer_size)

        if not os.path.exists(self.__file_path):
            raise FileNotFoundError(f"File {self.__file_path} does not exist.")

    @property
    def default_string_buffer_size(self):
        return self.__default_string_buffer_size

    @default_string_buffer_size.setter
    def default_string_buffer_size(self, val):
        if not isinstance(val, int) or int(val) <= 0:
            raise TypeError("Default string buffer size must be a positive, non-zero, integer.")

        if val < 32:
            self.__logger.warning("Setting the default string buffer size below 32 "
                                  "runs a higher risk of truncated data.")

        self.__default_string_buffer_size = val

    @property
    def cmud_file_handle(self):
        return self.__cmud_file_handle

    def __enter__(self):
        if self.__file_mode == 'r':
            self.__cmud_file_handle, _ = cmud.open_read(self.__file_path)
            return self
        else:
            raise NotImplementedError(f"Open mode '{self.__file_mode}' is not implemented. "
                                      f"Only read ('r') is currently supported.")

    def __exit__(self, exc_type, exc_val, exc_tb):
        cmud.close_read(self.__cmud_file_handle)

    def get_run_description(self) -> str:
        raise NotImplementedError()

    def get_experiment_number(self) -> int:
        raise NotImplementedError()

    def get_run_number(self) -> int:
        raise NotImplementedError()

    def get_elapsed_seconds(self) -> int:
        raise NotImplementedError()

    def get_time_begin(self) -> int:
        raise NotImplementedError()

    def get_time_end(self) -> int:
        raise NotImplementedError()

    def get_title(self) -> str:
        raise NotImplementedError()

    def get_lab(self) -> str:
        raise NotImplementedError()

    def get_area(self) -> str:
        raise NotImplementedError()

    def get_method(self) -> str:
        raise NotImplementedError()

    def get_apparatus(self) -> str:
        raise NotImplementedError()

    def get_insert(self) -> str:
        raise NotImplementedError()

    def get_sample(self) -> str:
        raise NotImplementedError()

    def get_orientation(self) -> str:
        raise NotImplementedError()

    def get_das(self) -> str:
        raise NotImplementedError()

    def get_experimenters(self) -> str:
        raise NotImplementedError()

    def get_temperature(self) -> float:
        raise NotImplementedError()

    def get_field(self) -> float:
        raise NotImplementedError()

    def get_subtitle(self) -> str:
        """Returns the subtitle, if any, for the file."""
        return cmud.get_subtitle(self.__cmud_file_handle, self.default_string_buffer_size)[1]

    def get_header_comments(self) -> tuple:
        """Returns the header comments, if any, for the file."""
        return (
            cmud.get_comment_1(self.__cmud_file_handle, self.default_string_buffer_size)[1],
            cmud.get_comment_2(self.__cmud_file_handle, self.default_string_buffer_size)[1],
            cmud.get_comment_3(self.__cmud_file_handle, self.default_string_buffer_size)[1]
        )

    def get_comments(self, body_buffer_size: int = 512) -> list:
        """Returns the comments, if any, for the file.

        Note that this does not include header comments."""
        _, _, num_comments = cmud.get_comments(self.__cmud_file_handle)

        return [
            cmud.get_comment(self.__cmud_file_handle, i, self.__default_string_buffer_size, body_buffer_size)
            for i in range(1, num_comments + 1)
        ]

    def get_histograms(self) -> HistogramCollection:
        raise NotImplementedError()
