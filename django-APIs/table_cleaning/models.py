# Some information on user access can be found here:
# https://developer.mozilla.org/en-US/docs/Learn/Server-side/Django/Authentication
# Information on optimizing time usage:
# https://stackoverflow.com/questions/1136106/what-is-an-efficient-way-of-inserting-thousands-of-records-into-an-sqlite-table/1136248

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.db import transaction
from model_utils.managers import InheritanceManager
import json
STR_CAP = 50


class ReinsurancePackage(models.Model):
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    package_name = models.CharField(max_length=200)


class XLLayer(models.Model):
    reinsurance_package = models.ForeignKey(ReinsurancePackage, on_delete=models.CASCADE)
    lb = models.FloatField()
    ub = models.FloatField()


class DataSheet(models.Model):
    reinsurance_package = models.ForeignKey(ReinsurancePackage, on_delete=models.CASCADE, blank=True, null=True)
    sheet_name = models.CharField(max_length=200)
    pub_date = models.DateTimeField('Date of insertion', default=timezone.now)
    is_aggregate = models.BooleanField(default=False)
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def read_entries(self, headers, row_vals, xls_types):
        chrono = 0
        #headers = [str(num+1).zfill(3) +". " + head for num, head in zip(range(len(headers)), headers)]

        with transaction.atomic():
            for row, type_row in zip(row_vals, xls_types):
                entry = Entry()
                entry.data_sheet_id = self.id
                entry.chrono = chrono
                chrono += 1
                entry.save()
                entry.put(headers, row, xls_types=type_row)
            self.save()

    def __str__(self):
        return self.sheet_name


class Entry(models.Model):
    data_sheet = models.ForeignKey(DataSheet, on_delete=models.CASCADE)
    pub_date = models.DateTimeField('Date of insertion', default=timezone.now)
    chrono = models.IntegerField(db_index=True)

    def put(self, headers, row, xls_types):
        for header, info, xls_type in zip(headers, row, xls_types):
            self.add_keyval(header, info, xls_type)

    def add_keyval(self, header, info, xls_type):
        if xls_type in [2, 6] and "." in str(info):
            self.keyval_set.add(FloatKeyVal.objects.create(key=header, value=info, super_data_sheet=self.data_sheet,
                                                           chrono=self.chrono, xls_type=xls_type, entry=self))
        elif xls_type in [2, 4, 6, 8]:
            self.keyval_set.add(IntKeyVal.objects.create(key=header, value=info, super_data_sheet=self.data_sheet,
                                                         chrono=self.chrono, xls_type=xls_type, entry=self))
        else:
            temp_info = info
            if len(str(temp_info)) > STR_CAP:
                temp_info = str(temp_info)[0:STR_CAP]
                self.data_sheet.sheetnotes_set.create(note=info)

            self.keyval_set.add(StringKeyVal.objects.create(key=header, value=temp_info, super_data_sheet=self.data_sheet,
                                                            chrono=self.chrono, xls_type=xls_type, entry=self))

class KeyVal(models.Model):
    # Here comes the options for the tags
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
    # Here comes the options for the data types
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
        (TRIANGLE_ELEMENT, "Triangle element")
    )
    super_data_sheet = models.ForeignKey(DataSheet, on_delete=models.CASCADE, null=True)
    key = models.CharField(max_length=STR_CAP, db_index=True)
    tag = models.CharField(max_length=3, choices=TAG_OPTIONS, default=UNDEFINED, db_index=True)

    entry = models.ForeignKey(Entry, on_delete=models.CASCADE)
    xls_type = models.IntegerField(default=1, choices=TYPE_OPTIONS)
    chrono = models.IntegerField(db_index=True)
    objects = InheritanceManager()

    def __str__(self):
        return self.key


class SheetNotes(models.Model):
    data_sheet = models.ForeignKey(DataSheet, on_delete=models.CASCADE, null=True)
    note = models.CharField(max_length=500, db_index=True)


class StringKeyVal(KeyVal):
    value = models.CharField(max_length=STR_CAP, db_index=True)


class IntKeyVal(KeyVal):
    value = models.IntegerField()


class FloatKeyVal(KeyVal):
    value = models.FloatField()


class Category(models.Model):
    url = models.CharField(max_length=240, db_index=True)
    name = models.CharField(max_length=240, db_index=True)

    def __str__(self):
        return self.name


class ReinsuranceContract(models.Model):
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=100, db_index=True)
    cb = models.OneToOneField(DataSheet, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.name

    def read_from_JSON(self, filename):
        with open(filename) as file:
            data = json.load(file)

        for key in data:
            self.contractclause_set.create(name=key, text=data[key])


class ContractClause(models.Model):
    name = models.CharField(max_length=1000, db_index=True, default="Clause Name")
    text = models.CharField(max_length=1000, db_index=True, default="Clause Text")
    contract = models.ForeignKey(ReinsuranceContract, on_delete=models.CASCADE)


class StopLossContract(models.Model):
    contract = models.OneToOneField(ReinsuranceContract, on_delete=models.CASCADE)
    line = models.IntegerField(default=0)


class UploadedDocument(models.Model):
    # CURRENCY_OPTIONS = (
    #     (1, "EUR"),
    #     (2, "USD"),
    #     (3, "JPY"),
    #     (4, "GBP"),
    #     (5, "AUD"),
    #     (6, "CAD"),
    #     (7, "CHF"),
    #     (8, "CNY"),
    #     (9, "SEK"),
    #     (10, "NZD")
    # )
    document = models.FileField(upload_to="table_cleaning/resources/uploads")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    # currency = models.IntegerField(choices=CURRENCY_OPTIONS, default=1, db_index=True)
    name = models.CharField(max_length=255, blank=True)