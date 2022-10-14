"""Provides a friendly interface to the C Mud library."""

import os

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

    def __init__(self, file, mode='r'):
        """Creates a MudFile object for interacting with mud files.

        Use with in a `with` statement to properly dispose of resources. Won't through an exception for improper files
        until you attempt to get data.

        :param file: Path to mud file
        :param mode: Mode for opening file
        :raises FileNotFoundError: File does not exist. Does not raise an error if the file is not correctly formatted.
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
        raise NotImplementedError()

    def get_comments(self) -> tuple:
        raise NotImplementedError()

    def get_histograms(self) -> HistogramCollection:
        raise NotImplementedError()
