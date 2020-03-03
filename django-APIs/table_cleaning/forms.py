from django import forms
from .services.sheet_manager import SheetManager
from python_back_end.utilities.sheet_io import ExcelLoader
from .models import KeyVal, UploadedDocument
from django.db import transaction



class SetTagsForm(forms.ModelForm):
    #message = forms.CharField(widget=forms.Textarea)
    class Meta:
        model = KeyVal
        fields = ('tag',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tag'] = forms.ChoiceField(choices=KeyVal.TAG_OPTIONS)
        self.fields['tag'].label = "bro"
        #self.fields['tag'].queryset = KeyVal.TAG_OPTIONS
        if "initial" in kwargs:
            if kwargs["initial"]:
                self.fields['tag'].initial = kwargs["initial"]["tag"]
                self.fields['tag'].label = kwargs["initial"]["label"]
        self.keys = []

    def set_tags(self, sheet, ind):
        print(self.cleaned_data)
        #if needed initialize keys
        if not self.keys:
            entry = sheet.entry_set.first()
            self.keys = [kv.key for kv in entry.keyval_set.order_by("key")]

        keyvals = sheet.keyval_set.filter(key=self.keys[ind])
        with transaction.atomic():
            for keyval in keyvals:
                if "tag" in self.cleaned_data:
                    keyval.tag=self.cleaned_data["tag"]
                else:
                    keyval.tag = "UN"

                keyval.save()


        #self.fields['city'].queryset = list()

class UploadForm(forms.ModelForm):
    class Meta:
        model = UploadedDocument
        fields = ('name', 'document')

    def load_data(self, filename):
        sr_list, dummy = ExcelLoader.load_excel(filename)
        return sr_list

    @staticmethod
    def push_to_sql_and_set_tags(sr, user, ex_pack):
        sheet = user.datasheet_set.create(sheet_name=sr.sheet_name, reinsurance_package=ex_pack)
        sheet.read_entries(sr.headers, sr.row_vals, sr.xls_types)
        print("Check")
        sm = SheetManager(sheet)
        sm.set_tags_from_headers()