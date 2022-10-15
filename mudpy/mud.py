"""Provides a friendly interface to the C Mud library."""
import os
import logging
import re

from mudpy import cmud


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

    def get_run_description(self) -> cmud.RunDescription:
        """Returns the complete run description."""
        return cmud.get_run_desc(self.__cmud_file_handle, self.__default_string_buffer_size)

    def get_experiment_number(self) -> int:
        """Returns the experiment number field."""
        return cmud.get_expt_number(self.__cmud_file_handle)[1]

    def get_run_number(self) -> int:
        """Returns the run number field."""
        return cmud.get_run_number(self.__cmud_file_handle)[1]

    def get_elapsed_seconds(self) -> int:
        """Returns the elapsed seconds field."""
        return cmud.get_elapsed_seconds(self.__cmud_file_handle)[1]

    def get_time_begin(self) -> int:
        """Returns the time begin field."""
        return cmud.get_time_begin(self.__cmud_file_handle)[1]

    def get_time_end(self) -> int:
        """Returns the time end field."""
        return cmud.get_time_end(self.__cmud_file_handle)[1]

    def get_title(self) -> str:
        """Returns the title field."""
        return cmud.get_title(self.__cmud_file_handle, self.__default_string_buffer_size)[1]

    def get_lab(self) -> str:
        """Returns the lab field."""
        return cmud.get_lab(self.__cmud_file_handle, self.__default_string_buffer_size)[1]

    def get_area(self) -> str:
        """Returns the area field."""
        return cmud.get_area(self.__cmud_file_handle, self.__default_string_buffer_size)[1]

    def get_method(self) -> str:
        """Returns the method field."""
        return cmud.get_method(self.__cmud_file_handle, self.__default_string_buffer_size)[1]

    def get_apparatus(self) -> str:
        """Returns the apparatus field."""
        return cmud.get_apparatus(self.__cmud_file_handle, self.__default_string_buffer_size)[1]

    def get_insert(self) -> str:
        """Returns the insert field."""
        return cmud.get_insert(self.__cmud_file_handle, self.__default_string_buffer_size)[1]

    def get_sample(self) -> str:
        """Returns the sample field."""
        return cmud.get_sample(self.__cmud_file_handle, self.__default_string_buffer_size)[1]

    def get_orientation(self) -> str:
        """Returns the orientation of the sample."""
        return cmud.get_orient(self.__cmud_file_handle, self.__default_string_buffer_size)[1]

    def get_das(self) -> str:
        """Returns the das (data acquisition system) field."""
        return cmud.get_das(self.__cmud_file_handle, self.__default_string_buffer_size)[1]

    def get_experimenters(self) -> str:
        """Returns the experimenter field."""
        return cmud.get_experimenter(self.__cmud_file_handle, self.__default_string_buffer_size)[1]

    def get_temperature(self) -> tuple:
        """Returns the temperature, with units."""
        temperature_with_units = cmud.get_temperature(self.__cmud_file_handle, self.__default_string_buffer_size)[1]
        temp_value = re.search(r"(\d*\.*\d*)", temperature_with_units)
        temp_units = re.search(r"([a-zA-Z]+)", temperature_with_units)

        if len(temp_value.groups()) == 0:
            return None, None
        value = temp_value.group(0)

        if len(temp_units.groups()) == 0:
            return value, None
        units = temp_units.group(0)

        return value, units

    def get_field(self) -> tuple:
        """Returns the magnetic field, with units."""
        field_with_units = cmud.get_field(self.__cmud_file_handle, self.__default_string_buffer_size)[1]
        field_value = re.search(r"(\d*\.*\d*)", field_with_units)
        field_units = re.search(r"([a-zA-Z]+)", field_with_units)

        if len(field_value.groups()) == 0:
            return None, None
        value = field_value.group(0)

        if len(field_units.groups()) == 0:
            return value, None
        units = field_units.group(0)

        return value, units

    def get_independent_variables(self):
        """Returns the independent variables, if any, for the file."""
        _, _, num_variables = cmud.get_ind_vars(self.__cmud_file_handle)

        if num_variables is None:
            return []

        return [
            cmud.get_ind_var(self.__cmud_file_handle, i, self.__default_string_buffer_size)
            for i in range(1, num_variables + 1)
        ]

    def get_scalers(self) -> list:
        """Returns the scalers, if any, for the file."""
        _, _, num_scalers = cmud.get_scalers(self.__cmud_file_handle)

        if num_scalers is None:
            return []

        return [
            cmud.get_scaler(self.__cmud_file_handle, i, self.__default_string_buffer_size)
            for i in range(1, num_scalers + 1)
        ]

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

        if num_comments is None:
            return []

        return [
            cmud.get_comment(self.__cmud_file_handle, i, self.__default_string_buffer_size, body_buffer_size)
            for i in range(1, num_comments + 1)
        ]

    def get_histograms(self) -> cmud.HistogramCollection:
        return cmud.get_histogram_collection(self.__cmud_file_handle, self.__default_string_buffer_size)
