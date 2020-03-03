class SheetTypeDefinitions:
    EMPTY_STRING = 0
    STRING = 1
    FLOAT = 2
    XL_DATE = 3
    BOOLEAN = 4
    ERROR = 5
    ZERO_FLOAT = 6
    STRING_DATE = 7
    ORDER = 8
    TRIANGLE_ELEMENT = 9
    ID_ELEMENT = 10
    TYPE_OPTIONS = (
        (EMPTY_STRING, "Empty string"),
        (STRING, "String"),
        (FLOAT, "Float"),
        (XL_DATE, "Excel date"),
        (BOOLEAN, "Boolean"),
        (ERROR, "Error"),
        (ZERO_FLOAT, "Zero float"),
        (STRING_DATE, "String"),
        (ORDER, "Order"),
        (TRIANGLE_ELEMENT, "Triangle element"),
        (ID_ELEMENT, "ID element")
    )

    UNDEFINED = "UN"
    EML = "EML"
    EMLTSIBAND = "ETB"
    PREMIUM = "PR"
    YEAR = "YR"
    NROBJ = "NR"
    TSI = "TSI"
    LOSS = "LO"
    ID = "ID"
    CAUSE = "CA"
    OCCUPANCY = "OC"
    OTHER = "OT"
    SEGMENT = "SEG"
    TAG = "TAG"
    TAG_OPTIONS = (
        (UNDEFINED, 'Undefined'),
        (EML, 'EML'),
        (EMLTSIBAND, 'EML/TSI band'),
        (PREMIUM, 'Premium income'),
        (YEAR, 'Year'),
        (NROBJ, '# of objects'),
        (TSI, 'TSI'),
        (LOSS, 'Loss'),
        (ID, 'Id'),
        (CAUSE, 'Cause'),
        (OCCUPANCY, 'Occupancy'),
        (SEGMENT, "Segment"),
        (TAG, "Tag"),
        (OTHER, 'Other')
    )