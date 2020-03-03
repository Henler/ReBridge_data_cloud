# This is a singleton module for controlling table_cleaning settings
import os
import multiprocessing


class PROGRAM_PARAMETERS:

    # Related to type col identification
    MIN_STRING_RATIO_CAT_COL = 0.5
    MIN_YEARS_SPANNED = 5
    MIN_STRING_RATIO_STRING_COL = 0.5
    MIN_STRING_RATIO_HOLLOW_STRING_COL = 0.1
    MIN_EMPTY_RATIO_HOLLOW_STRING_COL = 0.5
    MIN_NUM_RATIO_NUM_COL = 0.8
    MIN_ESS_RATIO_VALUE_COL = 0.01
    MIN_STRING_RATIO_CAT_ROW = 0.8

    # Related to triangle identification
    MAXIMAL_YEARS_SPANNED = 50
    TRIANGLE_THRESHOLD = 0.8
    MIN_SCORE_TURNED_TRIANGLE = 0.80
    MIN_TRIANGLE_SIMILARITY = 0.6
    MIN_ROWS_TRIANGLE = 6
    MIN_COLS_TRIANGLE = 5

    # Related to header managements
    N_POSSIBLE_HEADER_ROWS = 10
    N_DIGITS_HEADER_PADDING = 3

    # Related to raw data sheet manipulation
    MAX_VERTICAL_MERGE_DISTANCE = 0.55
    MAX_VERTICAL_MERGE_AVERAGE_DISTANCE = 0.5
    MAX_HORIZONTAL_MERGE_DISTANCE = 0.3
    DISTANCE_UNDEFINED_DEFAULT = 0.8
    MIN_LABEL_SIM = 0.85
    MIN_NUM_ROWS_DATA_SHEET = 8
    MIN_NUM_COLS_DATA_SHEET = 3

    # Related to date col identification/manipulation
    MIN_LENGTH_NORMAL_COL = 12
    MIN_DATE_RATIO_NORMAL_COL = 0.6
    MIN_DATE_RATIO_SHORT_COL = 0.6
    MIN_N_DATES_DATE_COL = 6
    MIN_RATIO_DATE_SIMILAR_COL = 0.8
    MIN_DIV_RATIO_MONTH_COL = 0.9

    # Related to sheet naming
    MIN_MEDIAN_DISTANCE = 3
    MAX_LENGTH_TO_RELATED_DATA = 20

    # Related to DataStruct chopping
    MAX_NUM_VERTICAL_CHOPS = 12
    MIN_VERTICAL_CHUNK_SIZE = 8
    MIN_HEADER_SIMILARITY = 0.5
    ACCEPTED_N_HORI_REPEATS = 8
    MIN_N_HORI_REPEATS = 4
    MAX_NUM_HORIZONTAL_CHOPS = 4

    # Related to DataHolder identification
    N_DESIRED_PER_SHEET = 3

    # Related to type col identififcation
    MAX_RATIO_LARGEST_CAT = 0.6
    MIN_RATIO_LARGEST_CAT = 0.1
    MAX_N_CATS = 10

    # logging
    LOG_SVM_FEATURES = False

    # Parallelism
    N_CORES = multiprocessing.cpu_count()

class PROGRAM_STRINGS:
    HEADER_PLACE_HOLDER = "XXYYXX"
    ORDER_COL_NAME = "Order at read-in"
    VERTICAL_YEAR_COL_NAME = "Vertical Years"
    CLAIMS_ID_COL_NAME = "Claims ID"
    SPECIAL_COL_NAME_LIST = [VERTICAL_YEAR_COL_NAME, CLAIMS_ID_COL_NAME]
    CAT_PAID_NAME = "Claim - Paid"
    CAT_RESERVED_NAME = "Claim - Reserved"
    CAT_INCURRED_NAME = "Claim - Incurred"
    CAT_PREMIUM_NAME = "Premium"
    TRANSFORMED_DATE_COL_NAME = " transformed"
    OUTPUT_NAME = "output_of_"


class PROGRAM_DIRECTORIES:
    RESOURCES_DIR = (os.path.dirname(os.path.realpath(__file__)).split("python_back_end")[0].replace('\\', '/') + "/resources/").replace('//', '/')
    TEMP_DIR = RESOURCES_DIR + "temp/"
    CONVERSION_DIR = RESOURCES_DIR + "conversion/"
    OUTER_SCOPE = os.path.dirname(os.path.realpath(__file__)).split("python_back_end")[0].replace('\\', '/')
    SVM_LOG_FILE = TEMP_DIR + "/temp.log"

