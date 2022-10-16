import sys
import os
import dataclasses
import ctypes
import logging
import enum
from typing import Tuple, Any, Union, Optional

import numpy as np

__logger = logging.getLogger(__name__)

shared_lib_path = "../mud/bin/mud.dll"

if not sys.platform.startswith('win32'):
    shared_lib_path = "../mud/bin/mud.so"

if not os.path.exists(shared_lib_path):
    raise Exception("Could not locate the mud library at {}".format(shared_lib_path))

mud_lib = ctypes.CDLL(shared_lib_path)


class Constants(enum.IntEnum):
    IND_VAR_ID = 16908293
    IND_VAR_ARR_ID = 16908294


@dataclasses.dataclass(frozen=True)
class Histogram:
    """Stores the data and header information for a histogram.
    """
    t0_ps: int
    t0_bin: int
    good_bin_one: int
    good_bin_two: int
    background_one: int
    background_two: int
    num_events: int
    title: str
    num: int
    data: np.ndarray
    # fixme time_data: np.ndarray what is this?


@dataclasses.dataclass(frozen=True)
class HistogramCollection:
    """Stores a collection of histograms with general histogram header information.

    This object can be indexed with either the histogram title or the histogram number. Important to note that the
    histograms are one-indexed in order to be consistent with the MUD library.
    """
    hist_type: int
    num_bytes: int
    num_bins: int
    bytes_per_bin: int
    fs_per_bin: int
    seconds_per_bin: int
    histograms: list

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
    experiment_number: int
    run_number: int
    time_begin: int
    time_end: int
    elapsed_seconds: int
    title: str
    lab: str
    area: str
    method: str
    apparatus: str
    insert: str
    sample: str
    orientation: str
    das: str
    experimenters: str
    temperature: str
    field: str
    subtitle: str
    comments: str


@dataclasses.dataclass(frozen=True)
class HistogramHeader:
    """Stores header information for a particular histogram."""
    hist_type: int
    num_bytes: int
    num_bins: int
    bytes_per_bin: int
    fs_per_bin: int
    t0_ps: int
    t0_bin: int
    good_bin_one: int
    good_bin_two: int
    background_one: int
    background_two: int
    num_events: int
    title: str


@dataclasses.dataclass(frozen=True)
class IndependentVariable:
    """Stores results for an independent variable.

    Note that historical_data and time_data will be None for most files."""
    low: float
    high: float
    mean: float
    std_dev: float
    skewness: float
    name: str
    description: str
    units: str
    historical_data: list
    time_data: int


@dataclasses.dataclass(frozen=True)
class Scaler:
    """Stores results for a scaler."""
    label: str
    count: int


@dataclasses.dataclass(frozen=True)
class Comment:
    """Stores information for the file's comments.

    Note that this does not refer to the comments in the file header.
    """
    time: int
    author: str
    title: str
    body: str


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


def open_read(filename: str) -> tuple:
    """Open mud file for reading.

    :param filename:
    :return:
    """
    c_filename = __to_bytes(filename)
    i_type = ctypes.c_int()
    fh = mud_lib.MUD_openRead(c_filename, ctypes.byref(i_type))
    return fh, i_type


def open_write(filename: str, w_type: int) -> int:
    """Open mud file for writing.

    :param filename:
    :param w_type:
    :return:
    """
    c_filename = __to_bytes(filename)
    i_type = ctypes.c_int(w_type)
    return mud_lib.MUD_openWrite(c_filename, i_type)


def open_read_write(filename: str) -> tuple:
    """Open mud file for reading and writing.

    :param filename:
    :return:
    """
    c_filename = __to_bytes(filename)
    i_type = ctypes.c_int()
    fh = mud_lib.MUD_openReadWrite(c_filename, ctypes.byref(i_type))
    return fh, i_type


def close_read(fh: int) -> int:
    """Close mud file for reading.

    :param fh:
    :return:
    """
    i_type = ctypes.c_int(fh)
    return mud_lib.MUD_closeRead(i_type)


def close_write(fh: int) -> int:
    """Close mud file for writing.

    :param fh:
    :return:
    """
    i_type = ctypes.c_int(fh)
    return mud_lib.MUD_closeWrite(i_type)


def close_write_file(fh: int, outfile: str) -> int:
    """Close mud file for reading and writing.

    :param fh:
    :param outfile:
    :return:
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


def get_run_desc(fh: int, string_section_max_length: int) -> RunDescription:
    """Get a run description summary.

    :param fh:
    :param string_section_max_length:
    :return:
    """
    return RunDescription(
        get_expt_number(fh)[0],
        get_run_number(fh)[0],
        get_time_begin(fh)[0],
        get_time_end(fh)[0],
        get_elapsed_seconds(fh)[0],
        get_title(fh, string_section_max_length)[0],
        get_lab(fh, string_section_max_length)[0],
        get_area(fh, string_section_max_length)[0],
        get_method(fh, string_section_max_length)[0],
        get_apparatus(fh, string_section_max_length)[0],
        get_insert(fh, string_section_max_length)[0],
        get_sample(fh, string_section_max_length)[0],
        get_orient(fh, string_section_max_length)[0],
        get_das(fh, string_section_max_length)[0],
        get_experimenter(fh, string_section_max_length)[0],
        get_temperature(fh, string_section_max_length)[0],
        get_field(fh, string_section_max_length)[0],
        get_subtitle(fh, string_section_max_length)[0],
        "FIXME Pass in comments"  # FIXME Pass in comments
    )


def get_expt_number(fh: int) -> tuple:
    """Get the experiment number.

    :param fh:
    :return:
    """
    return __get_integer_value(mud_lib.MUD_getExptNumber, fh)


def get_run_number(fh: int) -> tuple:
    """Get the run number.

    :param fh:
    :return:
    """
    return __get_integer_value(mud_lib.MUD_getRunNumber, fh)


def get_elapsed_seconds(fh: int) -> tuple:
    """Get the elapsed seconds.

    :param fh:
    :return:
    """
    return __get_integer_value(mud_lib.MUD_getElapsedSec, fh)


def get_time_begin(fh: int) -> tuple:
    """Get the beginning time.

    :param fh:
    :return:
    """
    return __get_integer_value(mud_lib.MUD_getTimeBegin, fh)


def get_time_end(fh: int) -> tuple:
    """Get the end time.

    :param fh:
    :return:
    """
    return __get_integer_value(mud_lib.MUD_getTimeEnd, fh)


def get_title(fh: int, length: int) -> tuple:
    """Get the title.

    :param fh:
    :param length:
    :return:
    """
    return __get_string_value(mud_lib.MUD_getTitle, fh, length)


def get_lab(fh: int, length: int) -> tuple:
    """Get the lab.

    :param fh:
    :param length:
    :return:
    """
    return __get_string_value(mud_lib.MUD_getLab, fh, length)


def get_area(fh: int, length: int) -> tuple:
    """Get the area.

    :param fh:
    :param length:
    :return:
    """
    return __get_string_value(mud_lib.MUD_getArea, fh, length)


def get_method(fh: int, length: int) -> tuple:
    """Get the method.

    :param fh:
    :param length:
    :return:
    """
    return __get_string_value(mud_lib.MUD_getMethod, fh, length)


def get_apparatus(fh: int, length: int) -> tuple:
    """Get the apparatus.

    :param fh:
    :param length:
    :return:
    """
    return __get_string_value(mud_lib.MUD_getApparatus, fh, length)


def get_insert(fh: int, length: int) -> tuple:
    """Get the insert.

    :param fh:
    :param length:
    :return:
    """
    return __get_string_value(mud_lib.MUD_getInsert, fh, length)


def get_sample(fh: int, length: int) -> tuple:
    """Get the sample.

    :param fh:
    :param length:
    :return:
    """
    return __get_string_value(mud_lib.MUD_getSample, fh, length)


def get_orient(fh: int, length: int) -> tuple:
    """Get the orientation of the sample.

    :param fh:
    :param length:
    :return:
    """
    return __get_string_value(mud_lib.MUD_getOrient, fh, length)


def get_das(fh: int, length: int) -> tuple:
    """Get the das (data acquisition system).

    :param fh:
    :param length:
    :return:
    """
    return __get_string_value(mud_lib.MUD_getDas, fh, length)


def get_experimenter(fh: int, length: int) -> tuple:
    """Get the experimenter.

    :param fh:
    :param length:
    :return:
    """
    return __get_string_value(mud_lib.MUD_getExperimenter, fh, length)


def get_temperature(fh: int, length: int) -> tuple:
    """Get the temperature.

    :param fh:
    :param length:
    :return:
    """
    return __get_string_value(mud_lib.MUD_getTemperature, fh, length)


def get_field(fh: int, length: int) -> tuple:
    """Get the field.

    :param fh:
    :param length:
    :return:
    """
    return __get_string_value(mud_lib.MUD_getField, fh, length)


def get_subtitle(fh: int, length: int) -> tuple:
    """Get the subtitle.

    :param fh:
    :param length:
    :return:
    """
    return __get_string_value(mud_lib.MUD_getSubtitle, fh, length)


def get_comment_1(fh: int, length: int) -> tuple:
    """Get the first file header comment.

    :param fh:
    :param length:
    :return:
    """
    return __get_string_value(mud_lib.MUD_getComment1, fh, length)


def get_comment_2(fh: int, length: int) -> tuple:
    """Get the second file header comment.

    :param fh:
    :param length:
    :return:
    """
    return __get_string_value(mud_lib.MUD_getComment2, fh, length)


def get_comment_3(fh: int, length: int) -> tuple:
    """Get the third file header comment.

    :param fh:
    :param length:
    :return:
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


def get_comments(fh: int):
    """Retrieves the type and number of comment groups.

    This does not include comments 1, 2 and 3 that are set in the file header.
    """
    __logger.info("cmud.get_comments (MUD_getComments) will not include comments in the file header.")
    return __get_integer_value_3(mud_lib.MUD_getComments, fh)


def get_comment(fh: int, num: int, short_length: int, long_length: int):
    """Get a particular comment for the file.

    :param fh:
    :param num:
    :param short_length:
    :param long_length:
    :return:
    """
    return Comment(
        get_comment_time(fh, num)[1],
        get_comment_author(fh, num, short_length)[1],
        get_comment_title(fh, num, short_length)[1],
        get_comment_body(fh, num, long_length)[1]
    )


def get_comment_prev(fh: int, num: int):
    """Get the number of the previous comment.

    :param fh:
    :param num:
    :return:
    """
    return __get_integer_value_2(mud_lib.MUD_getCommentPrev, fh, num)


def get_comment_next(fh: int, num: int):
    """Get the number of the next comment.

    :param fh:
    :param num:
    :return:
    """
    return __get_integer_value_2(mud_lib.MUD_getCommentNext, fh, num)


def get_comment_time(fh: int, num: int):
    """Get the time the comment was made.

    :param fh:
    :param num:
    :return:
    """
    return __get_integer_value_2(mud_lib.MUD_getCommentTime, fh, num)


def get_comment_author(fh: int, num: int, length: int):
    """Get the comment author.

    :param fh:
    :param num:
    :param length:
    :return:
    """
    return __get_string_value_2(mud_lib.MUD_getCommentAuthor, fh, num, length)


def get_comment_title(fh: int, num: int, length: int):
    """Get the comment title.

    :param fh:
    :param num:
    :param length:
    :return:
    """
    return __get_string_value_2(mud_lib.MUD_getCommentTitle, fh, num, length)


def get_comment_body(fh: int, num: int, length: int):
    """Get the comment body.

    :param fh:
    :param num:
    :param length:
    :return:
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


def get_hists(fh: int):
    """Get the number of histograms.

    :param fh:
    :return:
    """
    return __get_integer_value_3(mud_lib.MUD_getHists, fh)


def get_histogram_collection(fh, length):
    """Get the histogram collection for the file.

    :param fh:
    :param length:
    :return:
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


def get_histogram(fh: int, num: int, length: int):
    """Get a particular histogram.

    :param fh:
    :param num:
    :param length:
    :return:
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


def get_hist_type(fh: int, num: int):
    """Get the histogram type.

    :param fh:
    :param num:
    :return:
    """
    return __get_integer_value_2(mud_lib.MUD_getHistType, fh, num)


def get_hist_num_bytes(fh: int, num: int):
    """Get the number of bytes in the histogram.

    :param fh:
    :param num:
    :return:
    """
    return __get_integer_value_2(mud_lib.MUD_getHistNumBytes, fh, num)


def get_hist_num_bins(fh: int, num: int):
    """Get the number of bins in the histogram.

    :param fh:
    :param num:
    :return:
    """
    return __get_integer_value_2(mud_lib.MUD_getHistNumBins, fh, num)


def get_hist_bytes_per_bin(fh: int, num: int):
    """Get the number of bytes per bin for a histogram.

    :param fh:
    :param num:
    :return:
    """
    return __get_integer_value_2(mud_lib.MUD_getHistBytesPerBin, fh, num)


def get_hist_fs_per_bin(fh: int, num: int):
    """Get the number of fs per bin for a histogram.

    :param fh:
    :param num:
    :return:
    """
    return __get_integer_value_2(mud_lib.MUD_getHistFsPerBin, fh, num)


def get_hist_seconds_per_bin(fh: int, num: int):
    """Get the number of seconds per bin for a histogram.

    :param fh:
    :param num:
    :return:
    """
    return __get_integer_value_2(mud_lib.MUD_getHistFsPerBin, fh, num)


def get_hist_t0_ps(fh: int, num: int):
    """Get the ps of the t0 bin for a histogram.

    :param fh:
    :param num:
    :return:
    """
    return __get_integer_value_2(mud_lib.MUD_getHistT0_Ps, fh, num)


def get_hist_t0_bin(fh: int, num: int):
    """Get the t0 bin for a histogram.

    :param fh:
    :param num:
    :return:
    """
    return __get_integer_value_2(mud_lib.MUD_getHistT0_Bin, fh, num)


def get_hist_good_bin_1(fh: int, num: int):
    """Get the first good bin for a histogram.

    :param fh:
    :param num:
    :return:
    """
    return __get_integer_value_2(mud_lib.MUD_getHistGoodBin1, fh, num)


def get_hist_good_bin_2(fh: int, num: int):
    """Get the last good bin for a histogram.

    :param fh:
    :param num:
    :return:
    """
    return __get_integer_value_2(mud_lib.MUD_getHistGoodBin2, fh, num)


def get_hist_bkgd_1(fh: int, num: int):
    """Get the first background bin for a histogram.

    :param fh:
    :param num:
    :return:
    """
    return __get_integer_value_2(mud_lib.MUD_getHistBkgd1, fh, num)


def get_hist_bkgd_2(fh: int, num: int):
    """Get the last background bin for a histogram.

    :param fh:
    :param num:
    :return:
    """
    return __get_integer_value_2(mud_lib.MUD_getHistBkgd2, fh, num)


def get_hist_num_events(fh: int, num: int):
    """Get the number of events for a histogram.

    :param fh:
    :param num:
    :return:
    """
    return __get_integer_value_2(mud_lib.MUD_getHistNumEvents, fh, num)


def get_hist_title(fh: int, num: int, length: int):
    """Get the title for a histogram.

    :param fh:
    :param num:
    :param length:
    :return:
    """
    return __get_string_value_2(mud_lib.MUD_getHistTitle, fh, num, length)


def get_hist_data(fh: int, num: int, length: int):
    """Get the data for a histogram.

    :param fh:
    :param num:
    :param length:
    :return:
    """
    return __get_integer_array_value(mud_lib.MUD_getHistData, fh, num, length)


def get_hist_time_data(fh: int, num: int):
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


def get_scalers(fh: int):
    """Get the number of scalers.

    :param fh:
    :return:
    """
    return __get_integer_value_3(mud_lib.MUD_getScalers, fh)


def get_scaler(fh: int, num: int, length: int):
    """Get the information for a particular scaler.

    :param fh:
    :param num:
    :param length:
    :return:
    """
    return Scaler(
        get_scaler_label(fh, num, length)[1],
        get_scaler_counts(fh, num)[1]
    )


def get_scaler_label(fh: int, num: int, length: int):
    """Get the label for a scaler.

    :param fh:
    :param num:
    :param length:
    :return:
    """
    return __get_string_value_2(mud_lib.MUD_getScalerLabel, fh, num, length)


def get_scaler_counts(fh: int, num: int):
    """Get the counts for a scaler.

    :param fh:
    :param num:
    :return:
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


def get_ind_vars(fh: int):
    """Get the number of independent variables.

    :param fh:
    :return:
    """
    return __get_integer_value_3(mud_lib.MUD_getIndVars, fh)


def get_ind_var(fh: int, num: int, length: int):
    """Get the information for a independent variable.

    :param fh:
    :param num:
    :param length:
    :return:
    """
    return IndependentVariable(
        get_ind_var_low(fh, num)[1],
        get_ind_var_high(fh, num)[1],
        get_ind_var_mean(fh, num)[1],
        get_ind_var_stddev(fh, num)[1],
        get_ind_var_skewness(fh, num)[1],
        get_ind_var_name(fh, num, length)[1],
        get_ind_var_description(fh, num, length)[1],
        get_ind_var_units(fh, num, length)[1]
    )


def get_ind_var_low(fh: int, num: int):
    """Get the low value for an independent variable.

    :param fh:
    :param num:
    :return:
    """
    return __get_double_value(mud_lib.MUD_getIndVarLow, fh, num)


def get_ind_var_high(fh: int, num: int):
    """Get the high value for an independent variable.

    :param fh:
    :param num:
    :return:
    """
    return __get_double_value(mud_lib.MUD_getIndVarHigh, fh, num)


def get_ind_var_mean(fh: int, num: int):
    """Get the mean value for an independent variable.

    :param fh:
    :param num:
    :return:
    """
    return __get_double_value(mud_lib.MUD_getIndVarMean, fh, num)


def get_ind_var_stddev(fh: int, num: int):
    """Get the standard deviation for an independent variable.

    :param fh:
    :param num:
    :return:
    """
    return __get_double_value(mud_lib.MUD_getIndVarStddev, fh, num)


def get_ind_var_skewness(fh: int, num: int):
    """Get the skewness for an independent variable.

    :param fh:
    :param num:
    :return:
    """
    return __get_double_value(mud_lib.MUD_getIndVarSkewness, fh, num)


def get_ind_var_name(fh: int, num: int, length: int):
    """Get the name for an independent variable.

    :param fh:
    :param num:
    :param length:
    :return:
    """
    return __get_string_value_2(mud_lib.MUD_getIndVarName, fh, num, length)


def get_ind_var_description(fh: int, num: int, length: int):
    """Get the description for an independent variable.

    :param fh:
    :param num:
    :param length:
    :return:
    """
    return __get_string_value_2(mud_lib.MUD_getIndVarDescription, fh, num, length)


def get_ind_var_units(fh: int, num: int, length: int):
    """Get the units for an independent variable.

    :param fh:
    :param num:
    :param length:
    :return:
    """
    return __get_string_value_2(mud_lib.MUD_getIndVarUnits, fh, num, length)


def get_ind_var_num_data(fh: int, num: int):
    """TODO Unsure

    :param fh:
    :param num:
    :return:
    """
    return __get_integer_value_2(mud_lib.MUD_getIndVarNumData, fh, num)


def get_ind_var_elem_size(fh: int, num: int):
    """Get the element size for an independent variable.

    :param fh:
    :param num:
    :return:
    """
    return __get_integer_value_2(mud_lib.MUD_getIndVarElemSize, fh, num)


def get_ind_var_data_type(fh: int, num: int):
    """Get the independent variable data type.

    :param fh:
    :param num:
    :return:
    """
    return __get_integer_value_2(mud_lib.MUD_getIndVarDataType, fh, num)


def get_ind_var_has_time(fh: int, num: int):
    return __get_integer_value_2(mud_lib.MUD_getIndVarHasTime, fh, num)


def get_ind_var_data(fh: int, num: int, length: int):
    return __get_integer_array_value(mud_lib.MUD_getIndVarData, fh, num, length)


def get_ind_var_time_data(fh: int, num: int):
    return __get_integer_value_2(mud_lib.MUD_getIndVarTimeData, fh, num)


"""
MUD FILE INDEPENDENT VARIABLE SETTERS
"""
# TODO


"""
C METHOD ABSTRACTIONS
"""


def __to_bytes(string: str):
    """Converts string to a byte array."""
    return bytes(string, 'ascii')


def __from_bytes(byte_string: bytes, encoding: str):
    """Converts a byte array to a string."""
    return byte_string.strip(b'\x00').decode(encoding=encoding, errors="backslashreplace")


def __get_string_value(method, fh: int, length: int, encoding='latin-1') -> Union[tuple[Any, str], tuple[Any, None]]:
    """
    Used for this signature from mud library: (int fd, char* value, int strdim)

    :param method:
    :param fh:
    :param length:
    :param encoding:
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


def __get_string_value_2(method, fh: int, other: int, length: int, encoding='latin-1') -> Union[
    tuple[Any, str], tuple[Any, None]]:
    """
    Used for this signature from the mud library: (int fd, int a, char* value, int strdim)

    :param method:
    :param fh:
    :param other:
    :param length:
    :param encoding:
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


def __get_integer_value(method, fh: int) -> tuple[Any, Optional[Any], int]:
    """
    Used for this signature from the mud library: (int fd, UINT32* value)

    :param method:
    :param fh:
    :return:
    """
    i_fh = ctypes.c_int(fh)
    i_value = ctypes.c_int()
    ret = method(i_fh, ctypes.byref(i_value))
    value = i_value.value
    return (ret, None) if ret == 0 else (ret, value)


def __get_integer_value_2(method, fh: int, other: int) -> Union[tuple[Any, None], tuple[Any, int]]:
    """
    Used for this signature from the mud library: (int fd, int a, UINT32* value)

    :param method:
    :param fh:
    :param other:
    :return:
    """
    i_fh = ctypes.c_int(fh)
    i_other = ctypes.c_int(other)
    i_value = ctypes.c_int()
    ret = method(i_fh, i_other, ctypes.byref(i_value))
    value = i_value.value
    return (ret, None) if ret == 0 else (ret, value)


def __get_integer_value_3(method, fh: int) -> Union[tuple[Any, None, None], tuple[Any, int, int]]:
    """
    Used for this signature from the mud library: (int fd, UINT32* pType, UINT32* pNum)

    :param method:
    :param fh:
    :return:
    """
    i_fh = ctypes.c_int(fh)
    i_value_1 = ctypes.c_int()
    i_value_2 = ctypes.c_int()
    ret = method(i_fh, ctypes.byref(i_value_1), ctypes.byref(i_value_2))
    value_1 = i_value_1.value
    value_2 = i_value_2.value
    return (ret, None, None) if ret == 0 else (ret, value_1, value_2)


def __get_double_value(method, fh: int, other: int) -> tuple[Any, Optional[Any], float]:
    """
    Used for this signature from the mud library:
    (int fd, int a, REAL64* value) or (int fd, int a, double* value)

    :param method:
    :param fh:
    :param other:
    :return:
    """
    i_fh = ctypes.c_int(fh)
    i_other = ctypes.c_int(other)
    d_value = ctypes.c_double()
    ret = method(i_fh, i_other, ctypes.byref(d_value))
    value = d_value.value
    return (ret, None) if ret == 0 else (ret, value)


def __get_integer_array_value(method, fh: int, other: int, length: int, to_np_array: bool = True):
    """
    Used for this signature from the mud library: (int fd, int a, void* pData)

    :param method:
    :param fh:
    :param other:
    :param length:
    :return:
    """
    if length is None:
        raise TypeError("Cannot create integer array with length 'None'")

    i_fh = ctypes.c_int(fh)
    i_other = ctypes.c_int(other)
    v_data = (ctypes.c_int * length)()
    ret = method(i_fh, i_other, v_data)  # will throw exception if array is too short
    value = v_data if not to_np_array else np.array(v_data)

    return (ret, None) if ret == 0 else (ret, value)
