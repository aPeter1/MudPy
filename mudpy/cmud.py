import sys
import os
import dataclasses
import ctypes
import logging
import enum
from typing import Any, Union, Optional

import numpy as np

__logger = logging.getLogger(__name__)

shared_lib_path = "../mud/bin/mud.dll"

if not sys.platform.startswith('win32'):
    shared_lib_path = "../mud/bin/mud.so"

if not os.path.exists(shared_lib_path):
    raise Exception("Could not locate the mud library at {}".format(shared_lib_path))

mud_lib = ctypes.CDLL(shared_lib_path)


class Constants:
    class IndVarType(enum.IntEnum):
        IND_VAR_ID = 16908293
        IND_VAR_ARR_ID = 16908294

    class IndVarHistoricalDataType(enum.IntEnum):
        IND_VAR_INTEGER_HISTORICAL_DATA = 1
        IND_VAR_REAL_HISTORICAL_DATA = 2
        IND_VAR_STRING_HISTORICAL_DATA = 3


@dataclasses.dataclass(frozen=True)
class Histogram:
    """Stores the data and header information for a histogram.
    """
    t0_ps: Optional[int]
    t0_bin: Optional[int]
    good_bin_one: Optional[int]
    good_bin_two: Optional[int]
    background_one: Optional[int]
    background_two: Optional[int]
    num_events: Optional[int]
    title: Optional[str]
    num: Optional[int]
    data: np.ndarray
    # fixme time_data: np.ndarray what is this?


@dataclasses.dataclass(frozen=True)
class HistogramCollection:
    """Stores a collection of histograms with general histogram header information.

    This object can be indexed with either the histogram title or the histogram number. Important to note that the
    histograms are one-indexed in order to be consistent with the MUD library.
    """
    hist_type: Optional[int]
    num_bytes: Optional[int]
    num_bins: Optional[int]
    bytes_per_bin: Optional[int]
    fs_per_bin: Optional[int]
    seconds_per_bin: Optional[int]
    histograms: list

    def __iter__(self):
        raise NotImplementedError()

    def __getitem__(self, item):
        if isinstance(item, int):
            for hist in self.histograms:
                if hist.num == item:
                    return hist
        elif isinstance(item, str):
            item = item.lower()
            for hist in self.histograms:
                if hist.title.lower() == item:
                    return hist
        else:
            raise TypeError("HistogramCollection can only be indexed by histogram number (int) and title (str).")
        raise IndexError(f"Histogram with index '{item}' was not found.")


@dataclasses.dataclass(frozen=True)
class RunDescription:
    """Stores meta information for a particular run."""
    experiment_number: Optional[int]
    run_number: Optional[int]
    time_begin: Optional[int]
    time_end: Optional[int]
    elapsed_seconds: Optional[int]
    title: Optional[str]
    lab: Optional[str]
    area: Optional[str]
    method: Optional[str]
    apparatus: Optional[str]
    insert: Optional[str]
    sample: Optional[str]
    orientation: Optional[str]
    das: Optional[str]
    experimenters: Optional[str]
    temperature: Optional[str]
    field: Optional[str]
    subtitle: Optional[str]
    comments: Optional[str]


@dataclasses.dataclass(frozen=True)
class HistogramHeader:
    """Stores header information for a particular histogram."""
    hist_type: Optional[int]
    num_bytes: Optional[int]
    num_bins: Optional[int]
    bytes_per_bin: Optional[int]
    fs_per_bin: Optional[int]
    t0_ps: Optional[int]
    t0_bin: Optional[int]
    good_bin_one: Optional[int]
    good_bin_two: Optional[int]
    background_one: Optional[int]
    background_two: Optional[int]
    num_events: Optional[int]
    title: Optional[str]


@dataclasses.dataclass(frozen=True)
class IndependentVariable:
    """Stores results for an independent variable.

    Note that historical_data and time_data will be None for most files."""
    low: Optional[float]
    high: Optional[float]
    mean: Optional[float]
    std_dev: Optional[float]
    skewness: Optional[float]
    name: Optional[str]
    description: Optional[str]
    units: Optional[str]
    historical_data: Union[list[str], np.ndarray]
    time_data: Optional[int]


@dataclasses.dataclass(frozen=True)
class Scaler:
    """Stores results for a scaler."""
    label: Optional[str]
    count: Optional[int]


@dataclasses.dataclass(frozen=True)
class Comment:
    """Stores information for the file's comments.

    Note that this does not refer to the comments in the file header.
    """
    time: Optional[int]
    author: Optional[str]
    title: Optional[str]
    body: Optional[str]


"""
FILE OPEN/CLOSE OPERATIONS
"""
mud_lib.MUD_openRead.restype = ctypes.c_int
mud_lib.MUD_openRead.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_int)]
mud_lib.MUD_openWrite.restype = ctypes.c_int
mud_lib.MUD_openWrite.argtypes = [ctypes.c_char_p, ctypes.c_int]
mud_lib.MUD_openReadWrite.restype = ctypes.c_int
mud_lib.MUD_openReadWrite.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_int)]
mud_lib.MUD_closeRead.restype = ctypes.c_int
mud_lib.MUD_closeRead.argtypes = [ctypes.c_int]
mud_lib.MUD_closeWrite.restype = ctypes.c_int
mud_lib.MUD_closeWrite.argtypes = [ctypes.c_int]
mud_lib.MUD_closeWriteFile.restype = ctypes.c_int
mud_lib.MUD_closeWriteFile.argtypes = [ctypes.c_int, ctypes.c_char_p]


def open_read(filename: str) -> tuple[int, int]:
    """Open mud file for reading.

    :param filename: Full or relative path to the MUD file
    :return: MUD file handle (or -1 for failure) and the file type.
    """
    c_filename = __to_bytes(filename)
    i_type = ctypes.c_int()
    fh = mud_lib.MUD_openRead(c_filename, ctypes.byref(i_type))
    return fh, i_type.value


def open_write(filename: str, w_type: int) -> int:
    """Open mud file for writing.
    
    No changes will be written until close_write() is called.
    
    :param filename: Full or relative path to the MUD file
    :param w_type: The file type
    :return: MUD file handle (or -1 for failure)
    """
    c_filename = __to_bytes(filename)
    i_type = ctypes.c_int(w_type)
    return mud_lib.MUD_openWrite(c_filename, i_type)


def open_read_write(filename: str) -> tuple[int, int]:
    """Open mud file for reading and writing.

    No changes will be written until close_write() is called.
    
    :param filename: Full or relative path to the MUD file
    :return: MUD file handle (or -1 for failure) and the file type
    """
    c_filename = __to_bytes(filename)
    i_type = ctypes.c_int()
    fh = mud_lib.MUD_openReadWrite(c_filename, ctypes.byref(i_type))
    return fh, i_type.value


def close_read(fh: int) -> int:
    """Close mud file for reading. Any changes will be abandoned.

    :param fh: MUD file handle
    :return: MUD return status (0 for failure, 1 for success)
    """
    i_type = ctypes.c_int(fh)
    return mud_lib.MUD_closeRead(i_type)


def close_write(fh: int) -> int:
    """Close mud file for writing. Any changes will be written.

    :param fh: MUD file handle
    :return: MUD return status (0 for failure, 1 for success)
    """
    i_type = ctypes.c_int(fh)
    return mud_lib.MUD_closeWrite(i_type)


def close_write_file(fh: int, outfile: str) -> int:
    """Close mud file for reading and writing and save the file, and changes, to a new file.

    :param fh: MUD file handle
    :param outfile: The new file to write
    :return: MUD return status (0 for failure, 1 for success)
    """
    c_outfile = __to_bytes(outfile)
    i_type = ctypes.c_int(fh)
    return mud_lib.MUD_closeWriteFile(i_type, c_outfile)


"""
MUD FILE HEADER GETTERS
"""
mud_lib.MUD_getRunDesc.restype = ctypes.c_int
mud_lib.MUD_getRunDesc.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
mud_lib.MUD_getExptNumber.restype = ctypes.c_int
mud_lib.MUD_getExptNumber.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
mud_lib.MUD_getRunNumber.restype = ctypes.c_int
mud_lib.MUD_getRunNumber.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
mud_lib.MUD_getElapsedSec.restype = ctypes.c_int
mud_lib.MUD_getElapsedSec.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
mud_lib.MUD_getTimeBegin.restype = ctypes.c_int
mud_lib.MUD_getTimeBegin.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
mud_lib.MUD_getTimeEnd.restype = ctypes.c_int
mud_lib.MUD_getTimeEnd.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
mud_lib.MUD_getTitle.restype = ctypes.c_int
mud_lib.MUD_getTitle.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int]
mud_lib.MUD_getLab.restype = ctypes.c_int
mud_lib.MUD_getLab.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int]
mud_lib.MUD_getArea.restype = ctypes.c_int
mud_lib.MUD_getArea.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int]
mud_lib.MUD_getMethod.restype = ctypes.c_int
mud_lib.MUD_getMethod.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int]
mud_lib.MUD_getApparatus.restype = ctypes.c_int
mud_lib.MUD_getApparatus.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int]
mud_lib.MUD_getInsert.restype = ctypes.c_int
mud_lib.MUD_getInsert.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int]
mud_lib.MUD_getSample.restype = ctypes.c_int
mud_lib.MUD_getSample.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int]
mud_lib.MUD_getOrient.restype = ctypes.c_int
mud_lib.MUD_getOrient.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int]
mud_lib.MUD_getDas.restype = ctypes.c_int
mud_lib.MUD_getDas.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int]
mud_lib.MUD_getExperimenter.restype = ctypes.c_int
mud_lib.MUD_getExperimenter.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int]
mud_lib.MUD_getTemperature.restype = ctypes.c_int
mud_lib.MUD_getTemperature.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int]
mud_lib.MUD_getField.restype = ctypes.c_int
mud_lib.MUD_getField.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int]
mud_lib.MUD_getSubtitle.restype = ctypes.c_int
mud_lib.MUD_getSubtitle.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int]
mud_lib.MUD_getComment1.restype = ctypes.c_int
mud_lib.MUD_getComment1.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int]
mud_lib.MUD_getComment2.restype = ctypes.c_int
mud_lib.MUD_getComment2.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int]
mud_lib.MUD_getComment3.restype = ctypes.c_int
mud_lib.MUD_getComment3.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int]


def get_run_desc(fh: int, length: int) -> RunDescription:
    """Get a run description summary.

    :param fh: MUD file handle
    :param length: Maximum buffer size to allocate for strings
    :return: A run description summary object
    """
    return RunDescription(
        get_expt_number(fh)[1],
        get_run_number(fh)[1],
        get_time_begin(fh)[1],
        get_time_end(fh)[1],
        get_elapsed_seconds(fh)[1],
        get_title(fh, length)[1],
        get_lab(fh, length)[1],
        get_area(fh, length)[1],
        get_method(fh, length)[1],
        get_apparatus(fh, length)[1],
        get_insert(fh, length)[1],
        get_sample(fh, length)[1],
        get_orient(fh, length)[1],
        get_das(fh, length)[1],
        get_experimenter(fh, length)[1],
        get_temperature(fh, length)[1],
        get_field(fh, length)[1],
        get_subtitle(fh, length)[1],
        "FIXME Pass in comments"  # FIXME Pass in comments
    )


def get_expt_number(fh: int) -> tuple[int, Optional[int]]:
    """Get the experiment number.

    :param fh: MUD file handle
    :return: MUD return status (0 for failure, 1 for success) and the experiment number
    """
    return __get_integer_value(mud_lib.MUD_getExptNumber, fh)


def get_run_number(fh: int) -> tuple[int, Optional[int]]:
    """Get the run number.

    :param fh: MUD file handle
    :return: MUD return status (0 for failure, 1 for success) and the run number
    """
    return __get_integer_value(mud_lib.MUD_getRunNumber, fh)


def get_elapsed_seconds(fh: int) -> tuple[int, Optional[int]]:
    """Get the elapsed seconds.

    :param fh: MUD file handle
    :return: MUD return status (0 for failure, 1 for success) and the elapsed seconds
    """
    return __get_integer_value(mud_lib.MUD_getElapsedSec, fh)


def get_time_begin(fh: int) -> tuple[int, Optional[int]]:
    """Get the beginning time as seconds from epoch.

    :param fh: MUD file handle
    :return: MUD return status (0 for failure, 1 for success) and the beginning time
    """
    return __get_integer_value(mud_lib.MUD_getTimeBegin, fh)


def get_time_end(fh: int) -> tuple[int, Optional[int]]:
    """Get the end time as seconds from epoch.

    :param fh: MUD file handle
    :return: MUD return status (0 for failure, 1 for success) and the end time
    """
    return __get_integer_value(mud_lib.MUD_getTimeEnd, fh)


def get_title(fh: int, length: int) -> tuple[int, Optional[str]]:
    """Get the title.

    :param fh: MUD file handle
    :param length: Maximum buffer size to allocate for string
    :return: MUD return status (0 for failure, 1 for success) and the title
    """
    return __get_string_value(mud_lib.MUD_getTitle, fh, length)


def get_lab(fh: int, length: int) -> tuple[int, Optional[str]]:
    """Get the lab.

    :param fh: MUD file handle
    :param length: Maximum buffer size to allocate for string
    :return: MUD return status (0 for failure, 1 for success) and the lab
    """
    return __get_string_value(mud_lib.MUD_getLab, fh, length)


def get_area(fh: int, length: int) -> tuple[int, Optional[str]]:
    """Get the area.

    :param fh: MUD file handle
    :param length: Maximum buffer size to allocate for string
    :return: MUD return status (0 for failure, 1 for success) and the area
    """
    return __get_string_value(mud_lib.MUD_getArea, fh, length)


def get_method(fh: int, length: int) -> tuple[int, Optional[str]]:
    """Get the method.

    :param fh: MUD file handle
    :param length: Maximum buffer size to allocate for string
    :return: MUD return status (0 for failure, 1 for success) and the method
    """
    return __get_string_value(mud_lib.MUD_getMethod, fh, length)


def get_apparatus(fh: int, length: int) -> tuple[int, Optional[str]]:
    """Get the apparatus.

    :param fh: MUD file handle
    :param length: Maximum buffer size to allocate for string
    :return: MUD return status (0 for failure, 1 for success) and the apparatus
    """
    return __get_string_value(mud_lib.MUD_getApparatus, fh, length)


def get_insert(fh: int, length: int) -> tuple[int, Optional[str]]:
    """Get the insert.

    :param fh: MUD file handle
    :param length: Maximum buffer size to allocate for string
    :return: MUD return status (0 for failure, 1 for success) and the insert
    """
    return __get_string_value(mud_lib.MUD_getInsert, fh, length)


def get_sample(fh: int, length: int) -> tuple[int, Optional[str]]:
    """Get the sample.

    :param fh: MUD file handle
    :param length: Maximum buffer size to allocate for string
    :return: MUD return status (0 for failure, 1 for success) and the sample
    """
    return __get_string_value(mud_lib.MUD_getSample, fh, length)


def get_orient(fh: int, length: int) -> tuple[int, Optional[str]]:
    """Get the orientation of the sample.

    :param fh: MUD file handle
    :param length: Maximum buffer size to allocate for string
    :return: MUD return status (0 for failure, 1 for success) and the orientation
    """
    return __get_string_value(mud_lib.MUD_getOrient, fh, length)


def get_das(fh: int, length: int) -> tuple[int, Optional[str]]:
    """Get the das (data acquisition system).

    :param fh: MUD file handle
    :param length: Maximum buffer size to allocate for string
    :return: MUD return status (0 for failure, 1 for success) and the das
    """
    return __get_string_value(mud_lib.MUD_getDas, fh, length)


def get_experimenter(fh: int, length: int) -> tuple[int, Optional[str]]:
    """Get the experimenter.

    :param fh: MUD file handle
    :param length: Maximum buffer size to allocate for string
    :return: MUD return status (0 for failure, 1 for success) and the experimenter(s)
    """
    return __get_string_value(mud_lib.MUD_getExperimenter, fh, length)


def get_temperature(fh: int, length: int) -> tuple[int, Optional[str]]:
    """Get the temperature (with units) as a string.

    :param fh: MUD file handle
    :param length: Maximum buffer size to allocate for string
    :return: MUD return status (0 for failure, 1 for success) and the temperature
    """
    return __get_string_value(mud_lib.MUD_getTemperature, fh, length)


def get_field(fh: int, length: int) -> tuple[int, Optional[str]]:
    """Get the field (with units) as a string.

    :param fh: MUD file handle
    :param length: Maximum buffer size to allocate for string
    :return: MUD return status (0 for failure, 1 for success) and the field
    """
    return __get_string_value(mud_lib.MUD_getField, fh, length)


def get_subtitle(fh: int, length: int) -> tuple[int, Optional[str]]:
    """Get the subtitle.

    :param fh: MUD file handle
    :param length: Maximum buffer size to allocate for string
    :return: MUD return status (0 for failure, 1 for success) and the subtitle
    """
    return __get_string_value(mud_lib.MUD_getSubtitle, fh, length)


def get_comment_1(fh: int, length: int) -> tuple[int, Optional[str]]:
    """Get the first file header comment.

    :param fh: MUD file handle
    :param length: Maximum buffer size to allocate for string
    :return: MUD return status (0 for failure, 1 for success) and the first header comment
    """
    return __get_string_value(mud_lib.MUD_getComment1, fh, length)


def get_comment_2(fh: int, length: int) -> tuple[int, Optional[str]]:
    """Get the second file header comment.

    :param fh: MUD file handle
    :param length: Maximum buffer size to allocate for string
    :return: MUD return status (0 for failure, 1 for success) and the second header comment
    """
    return __get_string_value(mud_lib.MUD_getComment2, fh, length)


def get_comment_3(fh: int, length: int) -> tuple[int, Optional[str]]:
    """Get the third file header comment.

    :param fh: MUD file handle
    :param length: Maximum buffer size to allocate for string
    :return: MUD return status (0 for failure, 1 for success) and the third header comment
    """
    return __get_string_value(mud_lib.MUD_getComment3, fh, length)


"""
MUD FILE HEADER SETTERS
"""
# TODO


"""
MUD FILE COMMENT GETTERS
"""
mud_lib.MUD_getComments.restype = ctypes.c_int
mud_lib.MUD_getComments.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int)]
mud_lib.MUD_getCommentPrev.restype = ctypes.c_int
mud_lib.MUD_getCommentPrev.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
mud_lib.MUD_getCommentNext.restype = ctypes.c_int
mud_lib.MUD_getCommentNext.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
mud_lib.MUD_getCommentTime.restype = ctypes.c_int
mud_lib.MUD_getCommentTime.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
mud_lib.MUD_getCommentAuthor.restype = ctypes.c_int
mud_lib.MUD_getCommentAuthor.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_char_p, ctypes.c_int]
mud_lib.MUD_getCommentTitle.restype = ctypes.c_int
mud_lib.MUD_getCommentTitle.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_char_p, ctypes.c_int]
mud_lib.MUD_getCommentBody.restype = ctypes.c_int
mud_lib.MUD_getCommentBody.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_char_p, ctypes.c_int]


# TODO Confirm functionality. Due to the underutilized nature of comments, we need to make our own.


def get_comments(fh: int) -> tuple[int, Optional[int], Optional[int]]:
    """Retrieves the type and number of comment groups.

    This does not include comments 1, 2 and 3 that are set in the file header.

    :param fh: MUD file handle
    :return: MUD return status (0 for failure, 1 for success), the comment group type and the number of comments
    """
    __logger.info("cmud.get_comments (MUD_getComments) will not include comments in the file header.")
    return __get_integer_value_3(mud_lib.MUD_getComments, fh)


def get_comment(fh: int, num: int, short_length: int, long_length: int) -> Comment:
    """Get a particular comment for the file.

    :param fh: MUD file handle
    :param num: The comment index (one-indexed)
    :param short_length: Maximum buffer size to allocate for string fields that are not the body
    :param long_length: Maximum buffer size to allocate for the body
    :return: A comment
    """
    return Comment(
        get_comment_time(fh, num)[1],
        get_comment_author(fh, num, short_length)[1],
        get_comment_title(fh, num, short_length)[1],
        get_comment_body(fh, num, long_length)[1]
    )


def get_comment_prev(fh: int, num: int) -> tuple[int, Optional[int]]:
    """Get the index of the previous comment.

    :param fh: MUD file handle
    :param num: The comment index (one-indexed)
    :return: MUD return status (0 for failure, 1 for success) and the index of the previous comment
    """
    return __get_integer_value_2(mud_lib.MUD_getCommentPrev, fh, num)


def get_comment_next(fh: int, num: int) -> tuple[int, Optional[int]]:
    """Get the index of the next comment.

    :param fh: MUD file handle
    :param num: The comment index (one-indexed)
    :return: MUD return status (0 for failure, 1 for success) and the index of the next comment
    """
    return __get_integer_value_2(mud_lib.MUD_getCommentNext, fh, num)


def get_comment_time(fh: int, num: int) -> tuple[int, Optional[int]]:
    """Get the time the comment was made as seconds from epoch.

    :param fh: MUD file handle
    :param num: The comment index (one-indexed)
    :return: MUD return status (0 for failure, 1 for success) and the time the comment was made
    """
    return __get_integer_value_2(mud_lib.MUD_getCommentTime, fh, num)


def get_comment_author(fh: int, num: int, length: int) -> tuple[int, Optional[str]]:
    """Get the comment author.

    :param fh: MUD file handle
    :param num: The comment index (one-indexed)
    :param length: Maximum buffer size to allocate for string
    :return: MUD return status (0 for failure, 1 for success) and the comment author
    """
    return __get_string_value_2(mud_lib.MUD_getCommentAuthor, fh, num, length)


def get_comment_title(fh: int, num: int, length: int) -> tuple[int, Optional[str]]:
    """Get the comment title.

    :param fh: MUD file handle
    :param num: The comment index (one-indexed)
    :param length: Maximum buffer size to allocate for string
    :return: MUD return status (0 for failure, 1 for success) and the comment title
    """
    return __get_string_value_2(mud_lib.MUD_getCommentTitle, fh, num, length)


def get_comment_body(fh: int, num: int, length: int) -> tuple[int, Optional[str]]:
    """Get the comment body.

    :param fh: MUD file handle
    :param num: The comment index (one-indexed)
    :param length: Maximum buffer size to allocate for string
    :return: MUD return status (0 for failure, 1 for success) and the comment body
    """
    return __get_string_value_2(mud_lib.MUD_getCommentBody, fh, num, length)


"""
MUD FILE COMMENT SETTERS
"""
# TODO


"""
MUD FILE DATA GETTERS
"""
mud_lib.MUD_getHists.restype = ctypes.c_int
mud_lib.MUD_getHists.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int)]
mud_lib.MUD_getHistType.restype = ctypes.c_int
mud_lib.MUD_getHistType.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
mud_lib.MUD_getHistNumBytes.restype = ctypes.c_int
mud_lib.MUD_getHistNumBytes.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
mud_lib.MUD_getHistNumBins.restype = ctypes.c_int
mud_lib.MUD_getHistNumBins.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
mud_lib.MUD_getHistBytesPerBin.restype = ctypes.c_int
mud_lib.MUD_getHistBytesPerBin.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
mud_lib.MUD_getHistFsPerBin.restype = ctypes.c_int
mud_lib.MUD_getHistFsPerBin.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
mud_lib.MUD_getHistSecondsPerBin.restype = ctypes.c_int
mud_lib.MUD_getHistSecondsPerBin.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_double)]
mud_lib.MUD_getHistT0_Ps.restype = ctypes.c_int
mud_lib.MUD_getHistT0_Ps.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
mud_lib.MUD_getHistT0_Bin.restype = ctypes.c_int
mud_lib.MUD_getHistT0_Bin.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
mud_lib.MUD_getHistGoodBin1.restype = ctypes.c_int
mud_lib.MUD_getHistGoodBin1.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
mud_lib.MUD_getHistGoodBin2.restype = ctypes.c_int
mud_lib.MUD_getHistGoodBin2.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
mud_lib.MUD_getHistBkgd1.restype = ctypes.c_int
mud_lib.MUD_getHistBkgd1.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
mud_lib.MUD_getHistBkgd2.restype = ctypes.c_int
mud_lib.MUD_getHistBkgd2.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
mud_lib.MUD_getHistNumEvents.restype = ctypes.c_int
mud_lib.MUD_getHistNumEvents.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
mud_lib.MUD_getHistTitle.restype = ctypes.c_int
mud_lib.MUD_getHistTitle.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_char_p, ctypes.c_int]
mud_lib.MUD_getHistData.restype = ctypes.c_int
mud_lib.MUD_getHistData.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_void_p]
mud_lib.MUD_getHistpData.restype = ctypes.c_int
mud_lib.MUD_getHistpData.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_void_p]
mud_lib.MUD_getHistTimeData.restype = ctypes.c_int
mud_lib.MUD_getHistTimeData.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
mud_lib.MUD_getHistpTimeData.restype = ctypes.c_int
mud_lib.MUD_getHistpTimeData.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_int)]


def get_hists(fh: int) -> tuple[int, Optional[int], Optional[int]]:
    """Retrieves the type and number of histograms.

    Note that type does not appear to affect the methods to retrieve data.

    :param fh: MUD file handle
    :return: MUD return status (0 for failure, 1 for success), the type and the number of histograms
    """
    return __get_integer_value_3(mud_lib.MUD_getHists, fh)


def get_histogram_collection(fh: int, length: int) -> Optional[HistogramCollection]:
    """Get the histogram collection for the file.

    This will read the histograms into memory.

    :param fh: MUD file handle
    :param length: Maximum buffer size to allocate for strings
    :return: A histogram collection
    """
    num_hists = get_hists(fh)[2]
    histograms = [get_histogram(fh, i+1, length) for i in range(num_hists)]

    if len(histograms) == 0:
        return None

    return HistogramCollection(
        get_hist_type(fh, 1)[1],
        get_hist_num_bytes(fh, 1)[1],
        get_hist_num_bins(fh, 1)[1],
        get_hist_bytes_per_bin(fh, 1)[1],
        get_hist_fs_per_bin(fh, 1)[1],
        get_hist_seconds_per_bin(fh, 1)[1],
        histograms
    )


def get_histogram(fh: int, num: int, length: int) -> Histogram:
    """Get a particular histogram.

    :param fh: MUD file handle
    :param num: The histogram index (one-indexed)
    :param length: Maximum buffer size to allocate for strings
    :return: A histogram
    """
    num_bins = get_hist_num_bins(fh, num)[1]

    return Histogram(
        get_hist_t0_ps(fh, num)[1],
        get_hist_t0_bin(fh, num)[1],
        get_hist_good_bin_1(fh, num)[1],
        get_hist_good_bin_2(fh, num)[1],
        get_hist_bkgd_1(fh, num)[1],
        get_hist_bkgd_2(fh, num)[1],
        get_hist_num_events(fh, num)[1],
        get_hist_title(fh, num, length)[1],
        num,
        get_hist_data(fh, num, num_bins),
    )


def get_hist_type(fh: int, num: int) -> tuple[int, Optional[int]]:
    """Get the histogram type.

    :param fh: MUD file handle
    :param num: The histogram index (one-indexed)
    :return: MUD return status (0 for failure, 1 for success) and the histogram type
    """
    return __get_integer_value_2(mud_lib.MUD_getHistType, fh, num)


def get_hist_num_bytes(fh: int, num: int) -> tuple[int, Optional[int]]:
    """Get the number of bytes for a histogram.

    :param fh: MUD file handle
    :param num: The histogram index (one-indexed)
    :return: MUD return status (0 for failure, 1 for success) and the number of bytes
    """
    return __get_integer_value_2(mud_lib.MUD_getHistNumBytes, fh, num)


def get_hist_num_bins(fh: int, num: int) -> tuple[int, Optional[int]]:
    """Get the number of bins for a histogram.

    :param fh: MUD file handle
    :param num: The histogram index (one-indexed)
    :return: MUD return status (0 for failure, 1 for success) and the number of bins
    """
    return __get_integer_value_2(mud_lib.MUD_getHistNumBins, fh, num)


def get_hist_bytes_per_bin(fh: int, num: int) -> tuple[int, Optional[int]]:
    """Get the number of bytes per bin for a histogram.

    :param fh: MUD file handle
    :param num: The histogram index (one-indexed)
    :return: MUD return status (0 for failure, 1 for success) and the bytes per bin
    """
    return __get_integer_value_2(mud_lib.MUD_getHistBytesPerBin, fh, num)


def get_hist_fs_per_bin(fh: int, num: int) -> tuple[int, Optional[int]]:
    """Get the number of fs per bin for a histogram.

    :param fh: MUD file handle
    :param num: The histogram index (one-indexed)
    :return: MUD return status (0 for failure, 1 for success) and the fs per bin
    """
    return __get_integer_value_2(mud_lib.MUD_getHistFsPerBin, fh, num)


def get_hist_seconds_per_bin(fh: int, num: int) -> tuple[int, Optional[int]]:
    """Get the number of seconds per bin for a histogram.

    :param fh: MUD file handle
    :param num: The histogram index (one-indexed)
    :return: MUD return status (0 for failure, 1 for success) and the seconds per bin
    """
    return __get_integer_value_2(mud_lib.MUD_getHistFsPerBin, fh, num)


def get_hist_t0_ps(fh: int, num: int) -> tuple[int, Optional[int]]:
    """Get the ps of the time-zero bin for a histogram.

    :param fh: MUD file handle
    :param num: The histogram index (one-indexed)
    :return: MUD return status (0 for failure, 1 for success) and the time-zero in ps
    """
    return __get_integer_value_2(mud_lib.MUD_getHistT0_Ps, fh, num)


def get_hist_t0_bin(fh: int, num: int) -> tuple[int, Optional[int]]:
    """Get the time-zero bin for a histogram.

    :param fh: MUD file handle
    :param num: The histogram index (one-indexed)
    :return: MUD return status (0 for failure, 1 for success) and the time-zero bin
    """
    return __get_integer_value_2(mud_lib.MUD_getHistT0_Bin, fh, num)


def get_hist_good_bin_1(fh: int, num: int) -> tuple[int, Optional[int]]:
    """Get the first good bin for a histogram.

    :param fh: MUD file handle
    :param num: The histogram index (one-indexed)
    :return: MUD return status (0 for failure, 1 for success) and the first good bin
    """
    return __get_integer_value_2(mud_lib.MUD_getHistGoodBin1, fh, num)


def get_hist_good_bin_2(fh: int, num: int) -> tuple[int, Optional[int]]:
    """Get the last good bin for a histogram.

    :param fh: MUD file handle
    :param num: The histogram index (one-indexed)
    :return: MUD return status (0 for failure, 1 for success) and last good bin
    """
    return __get_integer_value_2(mud_lib.MUD_getHistGoodBin2, fh, num)


def get_hist_bkgd_1(fh: int, num: int) -> tuple[int, Optional[int]]:
    """Get the first background bin for a histogram.

    :param fh: MUD file handle
    :param num: The histogram index (one-indexed)
    :return: MUD return status (0 for failure, 1 for success) and first background bin
    """
    return __get_integer_value_2(mud_lib.MUD_getHistBkgd1, fh, num)


def get_hist_bkgd_2(fh: int, num: int) -> tuple[int, Optional[int]]:
    """Get the last background bin for a histogram.

    :param fh: MUD file handle
    :param num: The histogram index (one-indexed)
    :return: MUD return status (0 for failure, 1 for success) and last background bin
    """
    return __get_integer_value_2(mud_lib.MUD_getHistBkgd2, fh, num)


def get_hist_num_events(fh: int, num: int) -> tuple[int, Optional[int]]:
    """Get the number of events for a histogram.

    :param fh: MUD file handle
    :param num: The histogram index (one-indexed)
    :return: MUD return status (0 for failure, 1 for success) and the number of event
    """
    return __get_integer_value_2(mud_lib.MUD_getHistNumEvents, fh, num)


def get_hist_title(fh: int, num: int, length: int) -> tuple[int, Optional[str]]:
    """Get the title for a histogram.

    :param fh: MUD file handle
    :param num: The histogram index (one-indexed)
    :param length: Maximum buffer size to allocate for string
    :return: MUD return status (0 for failure, 1 for success) and the title
    """
    return __get_string_value_2(mud_lib.MUD_getHistTitle, fh, num, length)


def get_hist_data(fh: int, num: int, length: int) -> tuple[int, Optional[np.ndarray]]:
    """Get the data for a histogram.

    :param fh: MUD file handle
    :param num: The histogram index (one-indexed)
    :param length: Length of histogram
    :return: MUD return status (0 for failure, 1 for success) and the histogram data
    """
    return __get_numeric_array_value(mud_lib.MUD_getHistData, fh, num, length, ctypes.c_int)


def get_hist_time_data(fh: int, num: int) -> tuple[int, Optional[int]]:
    """Get time data for histogram. FIXME

    :param fh: MUD file handle
    :param num: The histogram index (one-indexed)
    :return: MUD return status (0 for failure, 1 for success) and the time data
    """
    return __get_integer_value_2(mud_lib.MUD_getHistTimeData, fh, num)


"""
MUD FILE DATA SETTERS
"""
# TODO


"""
MUD FILE DATA PACKERS
"""
# TODO


"""
MUD FILE SCALER GETTERS
"""
mud_lib.MUD_getScalers.restype = ctypes.c_int
mud_lib.MUD_getScalers.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int)]
mud_lib.MUD_getScalerLabel.restype = ctypes.c_int
mud_lib.MUD_getScalerLabel.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_char_p, ctypes.c_int]
mud_lib.MUD_getScalerCounts.restype = ctypes.c_int
mud_lib.MUD_getScalerCounts.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_int)]


def get_scalers(fh: int) -> tuple[int, Optional[int], Optional[int]]:
    """Get the type and number of scalers.

    :param fh: MUD file handle
    :return: MUD return status (0 for failure, 1 for success), type and number of scalers
    """
    return __get_integer_value_3(mud_lib.MUD_getScalers, fh)


def get_scaler(fh: int, num: int, length: int) -> Scaler:
    """Get the information for a particular scaler.

    :param fh: MUD file handle
    :param num: The scaler index (one-indexed)
    :param length: Maximum buffer size to allocate for string
    :return: A scaler
    """
    return Scaler(
        get_scaler_label(fh, num, length)[1],
        get_scaler_counts(fh, num)[1]
    )


def get_scaler_label(fh: int, num: int, length: int) -> tuple[int, Optional[str]]:
    """Get the label for a scaler.

    :param fh: MUD file handle
    :param num: The scaler index (one-indexed)
    :param length: Maximum buffer size to allocate for string
    :return: MUD return status (0 for failure, 1 for success) and the scaler label
    """
    return __get_string_value_2(mud_lib.MUD_getScalerLabel, fh, num, length)


def get_scaler_counts(fh: int, num: int) -> tuple[int, Optional[int]]:
    """Get the counts for a scaler.

    :param fh: MUD file handle
    :param num: The scaler index (one-indexed)
    :return: MUD return status (0 for failure, 1 for success) and the scaler counts
    """
    return __get_integer_value_2(mud_lib.MUD_getScalerCounts, fh, num)


"""
MUD FILE SCALER SETTERS
"""
# TODO


"""
MUD FILE INDEPENDENT VARIABLE GETTERS
"""
mud_lib.MUD_getIndVars.restype = ctypes.c_int
mud_lib.MUD_getIndVars.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int)]
mud_lib.MUD_getIndVarLow.restype = ctypes.c_int
mud_lib.MUD_getIndVarLow.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_double)]
mud_lib.MUD_getIndVarHigh.restype = ctypes.c_int
mud_lib.MUD_getIndVarHigh.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_double)]
mud_lib.MUD_getIndVarMean.restype = ctypes.c_int
mud_lib.MUD_getIndVarMean.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_double)]
mud_lib.MUD_getIndVarStddev.restype = ctypes.c_int
mud_lib.MUD_getIndVarStddev.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_double)]
mud_lib.MUD_getIndVarSkewness.restype = ctypes.c_int
mud_lib.MUD_getIndVarSkewness.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_double)]
mud_lib.MUD_getIndVarName.restype = ctypes.c_int
mud_lib.MUD_getIndVarName.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_char_p, ctypes.c_int]
mud_lib.MUD_getIndVarDescription.restype = ctypes.c_int
mud_lib.MUD_getIndVarDescription.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_char_p, ctypes.c_int]
mud_lib.MUD_getIndVarUnits.restype = ctypes.c_int
mud_lib.MUD_getIndVarUnits.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_char_p, ctypes.c_int]
mud_lib.MUD_getIndVarNumData.restype = ctypes.c_int
mud_lib.MUD_getIndVarNumData.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
mud_lib.MUD_getIndVarElemSize.restype = ctypes.c_int
mud_lib.MUD_getIndVarElemSize.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
mud_lib.MUD_getIndVarDataType.restype = ctypes.c_int
mud_lib.MUD_getIndVarDataType.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
mud_lib.MUD_getIndVarHasTime.restype = ctypes.c_int
mud_lib.MUD_getIndVarHasTime.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
mud_lib.MUD_getIndVarData.restype = ctypes.c_int
mud_lib.MUD_getIndVarData.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_void_p]
mud_lib.MUD_getIndVarTimeData.restype = ctypes.c_int
mud_lib.MUD_getIndVarTimeData.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_int)]


def get_ind_vars(fh: int) -> tuple[int, Optional[int], Optional[int]]:
    """Get the type and number of independent variables.

    :param fh: MUD file handle
    :return: MUD return status (0 for failure, 1 for success), the type and number of independent variables
    """
    return __get_integer_value_3(mud_lib.MUD_getIndVars, fh)


def get_ind_var(fh: int, num: int, length: int) -> IndependentVariable:
    """Get the information for an independent variable.

    :param fh: MUD file handle
    :param num: The independent variable index (one-indexed)
    :param length: Maximum buffer size to allocate for strings
    :return: An independent variable
    """
    _, p_type, _ = get_ind_vars(fh)

    if p_type == Constants.IndVarType.IND_VAR_ARR_ID:

        if get_ind_var_has_time(fh, num)[1]:
            _, time_data = get_ind_var_time_data(fh, num)
        else:
            time_data = None

        _, data_type = get_ind_var_data_type(fh, num)
        _, num_data = get_ind_var_num_data(fh, num)
        _, elem_size = get_ind_var_elem_size(fh, num)
        _, historical_data = get_ind_var_data(fh, num, num_data, elem_size, data_type)
    else:
        historical_data, time_data = (None, None)

    return IndependentVariable(
        get_ind_var_low(fh, num)[1],
        get_ind_var_high(fh, num)[1],
        get_ind_var_mean(fh, num)[1],
        get_ind_var_stddev(fh, num)[1],
        get_ind_var_skewness(fh, num)[1],
        get_ind_var_name(fh, num, length)[1],
        get_ind_var_description(fh, num, length)[1],
        get_ind_var_units(fh, num, length)[1],
        historical_data,
        time_data
    )


def get_ind_var_low(fh: int, num: int) -> tuple[int, Optional[float]]:
    """Get the low value for an independent variable.

    :param fh: MUD file handle
    :param num: The independent variable index (one-indexed)
    :return: MUD return status (0 for failure, 1 for success) and the low value
    """
    return __get_double_value(mud_lib.MUD_getIndVarLow, fh, num)


def get_ind_var_high(fh: int, num: int) -> tuple[int, Optional[float]]:
    """Get the high value for an independent variable.

    :param fh: MUD file handle
    :param num: The independent variable index (one-indexed)
    :return: MUD return status (0 for failure, 1 for success) and the high value
    """
    return __get_double_value(mud_lib.MUD_getIndVarHigh, fh, num)


def get_ind_var_mean(fh: int, num: int) -> tuple[int, Optional[float]]:
    """Get the mean value for an independent variable.

    :param fh: MUD file handle
    :param num: The independent variable index (one-indexed)
    :return: MUD return status (0 for failure, 1 for success) and mean value
    """
    return __get_double_value(mud_lib.MUD_getIndVarMean, fh, num)


def get_ind_var_stddev(fh: int, num: int) -> tuple[int, Optional[float]]:
    """Get the standard deviation for an independent variable.

    :param fh: MUD file handle
    :param num: The independent variable index (one-indexed)
    :return: MUD return status (0 for failure, 1 for success) and the standard deviation
    """
    return __get_double_value(mud_lib.MUD_getIndVarStddev, fh, num)


def get_ind_var_skewness(fh: int, num: int) -> tuple[int, Optional[float]]:
    """Get the skewness for an independent variable.

    :param fh: MUD file handle
    :param num: The independent variable index (one-indexed)
    :return: MUD return status (0 for failure, 1 for success) and the skewness
    """
    return __get_double_value(mud_lib.MUD_getIndVarSkewness, fh, num)


def get_ind_var_name(fh: int, num: int, length: int) -> tuple[int, Optional[str]]:
    """Get the name for an independent variable.

    :param fh: MUD file handle
    :param num: The independent variable index (one-indexed)
    :param length: Maximum buffer size to allocate for string
    :return: MUD return status (0 for failure, 1 for success) and the name
    """
    return __get_string_value_2(mud_lib.MUD_getIndVarName, fh, num, length)


def get_ind_var_description(fh: int, num: int, length: int) -> tuple[int, Optional[str]]:
    """Get the description for an independent variable.

    :param fh: MUD file handle
    :param num: The independent variable index (one-indexed)
    :param length: Maximum buffer size to allocate for string
    :return: MUD return status (0 for failure, 1 for success) and the description
    """
    return __get_string_value_2(mud_lib.MUD_getIndVarDescription, fh, num, length)


def get_ind_var_units(fh: int, num: int, length: int) -> tuple[int, Optional[str]]:
    """Get the units for an independent variable.

    :param fh: MUD file handle
    :param num: The independent variable index (one-indexed)
    :param length: Maximum buffer size to allocate for string
    :return: MUD return status (0 for failure, 1 for success) and the units
    """
    return __get_string_value_2(mud_lib.MUD_getIndVarUnits, fh, num, length)


def get_ind_var_num_data(fh: int, num: int) -> tuple[int, Optional[int]]:
    """Gets the number of data points in the historical data.

    :param fh: MUD file handle
    :param num: The independent variable index (one-indexed)
    :return: MUD return status (0 for failure, 1 for success) and the number of historical datapoints
    """
    return __get_integer_value_2(mud_lib.MUD_getIndVarNumData, fh, num)


def get_ind_var_elem_size(fh: int, num: int) -> tuple[int, Optional[int]]:
    """Get the element size for an independent variable.

    :param fh: MUD file handle
    :param num: The independent variable index (one-indexed)
    :return: MUD return status (0 for failure, 1 for success) and size of the historical datapoint elements
    """
    return __get_integer_value_2(mud_lib.MUD_getIndVarElemSize, fh, num)


def get_ind_var_data_type(fh: int, num: int) -> tuple[int, Optional[Constants.IndVarHistoricalDataType]]:
    """Get the independent variable data type.

    :param fh: MUD file handle
    :param num: The independent variable index (one-indexed)
    :return: MUD return status (0 for failure, 1 for success) and the type of the historical data
    """
    return __get_integer_value_2(mud_lib.MUD_getIndVarDataType, fh, num)


def get_ind_var_has_time(fh: int, num: int) -> tuple[int, bool]:
    """Indicates if there is time data

    :param fh: MUD file handle
    :param num: The independent variable index (one-indexed)
    :return: MUD return status (0 for failure, 1 for success) and a boolean indicating if there is time data
    """
    ret, val = __get_integer_value_2(mud_lib.MUD_getIndVarHasTime, fh, num)
    return ret, False if val is None else val == 1


def get_ind_var_data(fh: int, num: int, length: int, elem_size: int, data_type: Constants.IndVarHistoricalDataType) \
        -> tuple[int, Optional[Union[list[str], np.ndarray]]]:
    """Returns the historical data of the independent variable, if any.

    :param elem_size: The number of bytes per element of data
    :param fh: MUD file handle
    :param num: The independent variable index (one-indexed)
    :param length: Length of array
    :param data_type: The type of the historical data
    :return: MUD return status (0 for failure, 1 for success) and the historical data
    """
    if data_type == Constants.IndVarHistoricalDataType.IND_VAR_INTEGER_HISTORICAL_DATA \
            or data_type == Constants.IndVarHistoricalDataType.IND_VAR_REAL_HISTORICAL_DATA:
        ctype_data_type = __numeric_ctype_from_size(elem_size, data_type ==
                                                    Constants.IndVarHistoricalDataType.IND_VAR_REAL_HISTORICAL_DATA)
        return __get_numeric_array_value(mud_lib.MUD_getIndVarData, fh, num, length, ctype_data_type)

    if data_type == Constants.IndVarHistoricalDataType.IND_VAR_STRING_HISTORICAL_DATA:
        return __get_string_array_value(mud_lib.MUD_getIndVarData, fh, num, length)


def get_ind_var_time_data(fh: int, num: int) -> tuple[int, Optional[int]]:
    """Get the time data for an independent variable as seconds since epoch.

    :param fh: MUD file handle
    :param num: The independent variable index (one-indexed)
    :return: MUD return status (0 for failure, 1 for success) and the time data
    """
    return __get_integer_value_2(mud_lib.MUD_getIndVarTimeData, fh, num)


"""
MUD FILE INDEPENDENT VARIABLE SETTERS
"""
# TODO


"""
C METHOD ABSTRACTIONS
"""


def __numeric_ctype_from_size(size: int, real: bool = False):
    """Given the byte size of the type and boolean real the method returns an appropriate ctype.

    :param size: The number of bytes for the type
    :param real: Boolean indicating if numeric value is real
    :return: A ctype data type (e.g. ctypes.c_int8)
    """
    if real:
        if size == 4:
            return ctypes.c_float
        elif size == 8:
            return ctypes.c_double
        elif size == 10:
            return ctypes.c_longdouble
    else:
        if size == 1:
            return ctypes.c_int8
        elif size == 2:
            return ctypes.c_int16
        elif size == 4:
            return ctypes.c_int32
        elif size == 8:
            return ctypes.c_int64
    raise Exception(f"Unable to determine the appropriate ctype for size {size} and real equals {real}")


def __to_bytes(string: str) -> bytes:
    """Converts string to a byte array."""
    return bytes(string, 'ascii')


def __from_bytes(byte_string: bytes, encoding: str) -> str:
    """Converts a byte array to a string."""
    return byte_string.strip(b'\x00').decode(encoding=encoding, errors="backslashreplace")


def __get_string_value(method, fh: int, length: int, encoding='latin-1') -> tuple[int, Optional[str]]:
    """
    Used for this signature from mud library: (int fd, char* value, int strdim)

    :param method: CTypes MUD function to call
    :param fh: MUD file handle
    :param length: Maximum buffer size to allocate for string
    :param encoding: String encoding
    :return: String value will be None if it is empty or whitespace only
    """
    i_fh = ctypes.c_int(fh)
    i_length = ctypes.c_int(length)
    c_value = bytes(length)
    ret = method(i_fh, c_value, i_length)
    value = __from_bytes(c_value, encoding)

    if value and not value.isspace():
        return ret, value
    else:
        return ret, None


def __get_string_value_2(method, fh: int, other: int, length: int, encoding='latin-1') -> tuple[int, Optional[str]]:
    """
    Used for this signature from the mud library: (int fd, int a, char* value, int strdim)

    :param method: CTypes MUD function to call
    :param fh: MUD file handle
    :param other: Miscellaneous parameter for method
    :param length: Maximum buffer size to allocate for string
    :param encoding: String encoding
    :return: String value will be None if it is empty or whitespace only
    """
    i_fh = ctypes.c_int(fh)
    i_other = ctypes.c_int(other)
    i_length = ctypes.c_int(length)
    c_value = bytes(length)
    ret = method(i_fh, i_other, c_value, i_length)
    value = __from_bytes(c_value, encoding)

    if value and not value.isspace():
        return ret, value
    else:
        return ret, None


def __get_integer_value(method, fh: int) -> tuple[int, Optional[int]]:
    """
    Used for this signature from the mud library: (int fd, UINT32* value)

    :param method: CTypes MUD function to call
    :param fh: MUD file handle
    :return: MUD return status (0 for failure, 1 for success) and an integer value
    """
    i_fh = ctypes.c_int(fh)
    i_value = ctypes.c_int()
    ret = method(i_fh, ctypes.byref(i_value))
    value = i_value.value
    return (ret, None) if ret == 0 else (ret, value)


def __get_integer_value_2(method, fh: int, other: int) -> tuple[int, Optional[int]]:
    """
    Used for this signature from the mud library: (int fd, int a, UINT32* value)

    :param method: CTypes MUD function to call
    :param fh: MUD file handle
    :param other: Miscellaneous parameter for method
    :return: MUD return status (0 for failure, 1 for success) and an integer value
    """
    i_fh = ctypes.c_int(fh)
    i_other = ctypes.c_int(other)
    i_value = ctypes.c_int()
    ret = method(i_fh, i_other, ctypes.byref(i_value))
    value = i_value.value
    return (ret, None) if ret == 0 else (ret, value)


def __get_integer_value_3(method, fh: int) -> tuple[int, Optional[int], Optional[int]]:
    """
    Used for this signature from the mud library: (int fd, UINT32* pType, UINT32* pNum)

    :param method: CTypes MUD function to call
    :param fh: MUD file handle
    :return: MUD return status (0 for failure, 1 for success) and two integer values
    """
    i_fh = ctypes.c_int(fh)
    i_value_1 = ctypes.c_int()
    i_value_2 = ctypes.c_int()
    ret = method(i_fh, ctypes.byref(i_value_1), ctypes.byref(i_value_2))
    value_1 = i_value_1.value
    value_2 = i_value_2.value
    return (ret, None, None) if ret == 0 else (ret, value_1, value_2)


def __get_double_value(method, fh: int, other: int) -> tuple[int, Optional[float]]:
    """
    Used for this signature from the mud library:
    (int fd, int a, REAL64* value) or (int fd, int a, double* value)

    :param method: CTypes MUD function to call
    :param fh: MUD file handle
    :param other: Miscellaneous parameter for method
    :return: MUD return status (0 for failure, 1 for success) and a float value
    """
    i_fh = ctypes.c_int(fh)
    i_other = ctypes.c_int(other)
    d_value = ctypes.c_double()
    ret = method(i_fh, i_other, ctypes.byref(d_value))
    value = d_value.value
    return (ret, None) if ret == 0 else (ret, value)


def __get_numeric_array_value(method, fh: int, other: int, length: int, datatype, to_np_array: bool = True):
    """
    Used for this signature from the mud library: (int fd, int a, void* pData) to retrieve numeric types.

    :param method: CTypes MUD function to call
    :param fh: MUD file handle
    :param other: Miscellaneous parameter for method
    :param length: Length of the array
    :param datatype: CType data type of numeric data
    :param to_np_array: Boolean indicating if the result should be converted to numpy array
    :return: MUD return status (0 for failure, 1 for success) and a numeric array
    """
    if length is None:
        raise TypeError("Cannot create numeric array with length 'None'")

    i_fh = ctypes.c_int(fh)
    i_other = ctypes.c_int(other)
    v_data = (datatype * length)()
    ret = method(i_fh, i_other, v_data)  # will throw exception if array is too short
    value = v_data if not to_np_array else np.array(v_data)

    return (ret, None) if ret == 0 else (ret, value)


def __get_string_array_value(method, fh: int, other: int, length: int, to_list: bool = True) -> tuple[int, list[str]]:
    """
    Used for this signature from the mud library: (int fd, int a, void* pData) to retrieve string types.

    :param method: CTypes MUD function to call
    :param fh: MUD file handle
    :param other: Miscellaneous parameter for method
    :param length: Length of the array
    :return: MUD return status (0 for failure, 1 for success) and a string array
    """
    if length is None:
        raise TypeError("Cannot create string array with length 'None'")

    i_fh = ctypes.c_int(fh)
    i_other = ctypes.c_int(other)
    v_data = (ctypes.c_char_p * length)()
    ret = method(i_fh, i_other, v_data)  # will throw exception if array is too short
    value = v_data if not to_list else list(v_data)

    return (ret, None) if ret == 0 else (ret, value)
