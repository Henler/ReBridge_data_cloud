from django.views import generic
from .models import DataSheet, ReinsuranceContract, KeyVal
from django.contrib.auth.mixins import LoginRequiredMixin
from python_back_end.data_cleaning.cleaning_pipeline import CleaningPipeline
from .services.sheet_manager import SheetManager
from python_back_end.utilities.sheet_io import SheetWriter
from .forms import SetTagsForm, UploadForm
from django.forms import formset_factory
from .services.output_utils import DataServer
from django.http import HttpResponseRedirect
from django.urls import reverse
from python_back_end.utilities.state_handling import DataHolder
from rest_framework.viewsets import ModelViewSet
import pandas as pd
from django.shortcuts import render, redirect
from .serializers import DataSheetSerializer
import os
import jsonpickle


class TableView(LoginRequiredMixin, generic.ListView):
    template_name = 'table_cleaning/tables.html'

    def get_context_data(self, **kwargs):
        # print("get context")
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        # Add in a QuerySet of all the books
        # print(context['cat_list'])
        return context

    def get_queryset(self):
        return DataSheet.objects.filter(owner=self.request.user).order_by('sheet_name')


class DataCleaningTableView(LoginRequiredMixin, generic.ListView):
    template_name = 'table_cleaning/data_cleaning_table.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.session.get('data_holder'):
            sr_list = jsonpickle.decode(self.request.session.get('data_holder'))
            data_holder = DataHolder()
            for sr in sr_list:
                data_holder.add_sheet(sr.sheet_name, pd.DataFrame(columns=sr.headers, data=sr.row_vals),
                             pd.DataFrame(columns=sr.headers, data=sr.xls_types))
            context["diff_dicts"], data_holder = CleaningPipeline.clean_data_dh(data_holder)
        else:
            sheets = DataSheet.objects.filter(owner=self.request.user).order_by('sheet_name')
            context["diff_dicts"], data_holder = CleaningPipeline.clean_data(sheets)
        #sheets = DataSheet.objects.filter(owner=self.request.user).order_by('sheet_name')
        #context["diff_dicts"], mem_dict = CleaningPipeline.clean_data(sheets)

        return context

    def get_queryset(self):
        return DataSheet.objects.filter(owner=self.request.user).order_by('sheet_name')


class TableDetailView(LoginRequiredMixin, generic.DetailView):
    model = DataSheet
    template_name = 'table_cleaning/table_detail.html'

    def get_context_data(self, **kwargs):
        # print("get context")
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        # Add in a QuerySet of all the books
        # print(self.request)
        # print(context)

        sm = SheetManager(context['datasheet'])
        context['headers'] = sm.get_sheet_headers()
        context['rows'] = sm.get_sheet_array()


        context['ordered_entries'] = context['datasheet'].entry_set.all().order_by('chrono')



        return context


class ContractDetailView(LoginRequiredMixin, generic.DetailView):
    model = ReinsuranceContract
    template_name = 'table_cleaning/contract_detail.html'

    def get_context_data(self, **kwargs):
        # print("get context")
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        # Add in a QuerySet of all the books
        # print(context['cat_list'])
        return context


class ChartsView(LoginRequiredMixin, generic.ListView):
    template_name = 'table_cleaning/charts.html'

    def get_context_data(self, **kwargs):
        # print("get context")
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        # Add in a QuerySet of all the books
        context['selected_datasheet'] = DataSheet.objects.get(sheet_name="St Erik Claims aggregated by Skadedatum")
        skade_entry = context['selected_datasheet'].entry_set.all().order_by('chrono')
        # print(context['cat_list'])
        skadedatum = []
        skade_value = []
        for entry in skade_entry:
            for keyval in entry.keyval_set.all():
                if keyval.key == "Skadedatum":
                    skadedatum.append(keyval.value)
                elif keyval.key == "Skadekostnad exkl. självrisk":
                    skade_value.append(keyval.value)
        context['skadedatum_all'] = skadedatum
        context['skadesumma_all'] = skade_value

        return context

    def get_queryset(self):
        return DataSheet.objects.filter(owner=self.request.user).order_by('sheet_name')


class DashboardView(LoginRequiredMixin, generic.ListView):
    template_name = 'table_cleaning/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def get_queryset(self):
        return DataSheet.objects.filter(owner=self.request.user).order_by('sheet_name')

    def post(self, request, *args, **kwargs):
        if request.method == 'POST':
            # try and write to excel
            path = "table_cleaning/resources/temp/"
            for sheet in self.get_queryset():
                sw = SheetWriter(sheet)
                sw.write_excel(path + sheet.sheet_name + ".xlsx")


        return redirect('/table_cleaning/dashboard')


class CustomerView(generic.ListView):
    template_name = 'table_cleaning/customer.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def get_queryset(self):
        return DataSheet.objects.filter(owner=self.request.user).order_by('sheet_name')


class MessageView(LoginRequiredMixin, generic.ListView):
    template_name = 'table_cleaning/messages.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def get_queryset(self):
        return DataSheet.objects.filter(owner=self.request.user).order_by('sheet_name')


class NewExposureView(LoginRequiredMixin, generic.edit.FormView, generic.ListView):
    template_name = 'table_cleaning/new_exposure.html'
    form_class = UploadForm
    success_url = '/table_cleaning/upload_data'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def get_queryset(self):
        return DataSheet.objects.filter(owner=self.request.user).order_by('sheet_name')

    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.

        #form.reload()
        return super().form_valid(form)

    def post(self, request, *args, **kwargs):
        if request.method == 'POST':
            form = UploadForm(request.POST, request.FILES)
            if form.is_valid():
                instance = form.save()
                sr = form.load_data(instance.document.name)
                request.session['data_holder'] = jsonpickle.encode(sr)
                os.remove(instance.document.name)
                instance.delete()

                return redirect('/table_cleaning/upload_data')
        else:
            form = UploadForm()
        return render(request, '/table_cleaning/create_triangle_table', {
            'form': form
        })



class TagDataView(LoginRequiredMixin, generic.edit.FormView, generic.ListView):
    template_name = 'table_cleaning/tag_data.html'
    #tag_formsetset = [formset_factory(SetTagsForm, extra=3)]
    form_class = SetTagsForm
    tag_formsetset = []
    tag_formset = formset_factory(SetTagsForm, extra=0)
    sheet_inds = []
    sheet_table_snippets = []
    success_url = '/table_cleaning/define_columns'

    def get_context_data(self, **kwargs):
        sheets = self.get_queryset()
        self.tag_formsetset.clear()
        self.sheet_inds.clear()
        for sheet, i in zip(sheets, range(len(sheets))):
            self.sheet_inds.append(i)
            sm = SheetManager(sheet)
            self.sheet_table_snippets.append([sm.get_sheet_headers(), sm.get_sheet_array_snippet()])
            tags = sm.get_sheet_short_tags()
            tag_list = [{'tag': tag, "label" : header} for tag, header in zip(tags, sm.get_sheet_headers())]
            instances = self.tag_formset(initial=tag_list)
            self.tag_formsetset.append(instances)
        context = super().get_context_data(**kwargs)
        context["KeyVal"] = KeyVal
        context["form_set"] = self.tag_formsetset
        #This is the magic complicated list that we will loop over in the template
        context["combined"] = zip(context["datasheet_list"], self.tag_formsetset, self.sheet_inds, self.sheet_table_snippets)
        return context

    def get_queryset(self):
        return DataSheet.objects.filter(owner=self.request.user).order_by('sheet_name')

    def post(self, request, *args, **kwargs):
        sheets = self.get_queryset()
        assert len(sheets) == len(self.tag_formsetset)
        #get the index of the request
        ind = int(self.request.POST["sheet_ind"])
        #for formset, sheet in zip(self.tag_formsetset, sheets):
        formset_req, sheet = self.tag_formset, sheets[ind]
        tag_formset = formset_req(self.request.POST)
        # Checking the if the form is valid
        if tag_formset.is_valid():

            for form, ind in zip(tag_formset, range(len(tag_formset))):
                form.set_tags(sheet, ind)
            return HttpResponseRedirect(reverse('table_cleaning:tag_data'))


class AnalyzeDataView(LoginRequiredMixin, generic.ListView):
    template_name = 'table_cleaning/analyze_data.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        #generate context for tables
        ds = DataServer(self.request.user.reinsurancepackage_set.first())
        context["histogram_layer_detail"] = ds.histogram_layer_detail_context()
        context["table_layer_loss"] = ds.table_layer_loss_context()
        context["table_premium_segment"] = ds.table_premium_segment_context()
        losses = [context["table_layer_loss"]["layer_losses"][i][-1][0] for i in range(len(context["table_layer_loss"]["layer_losses"]))]
        context["table_burning_cost"] = ds.table_burning_cost_context(losses)
        #Very dirty fix to remove tuples from table_layer_losses. Not sure if used for other things but tuples not suitable for rendering front end
        for layer in context["table_layer_loss"]["layer_losses"]:
            layer[:] = [x[0] for x in layer] 

        table_layer_objects = ds.table_layer_count_context()
        context["table_layer_objects"] = table_layer_objects
        table_layer_objects_rows = []
        for a in zip(*table_layer_objects.values()):
            table_layer_objects_rows.append(list(a))

        context["table_layer_objects_rows"] = table_layer_objects_rows

        return context

    def get_queryset(self):
        return DataSheet.objects.filter(owner=self.request.user).order_by('sheet_name')


class ChartData(ModelViewSet):
    serializer_class = DataSheetSerializer
    #queryset = DataSheet.objects.all()

    # def dispatch(self, request, *args, **kwargs):
    #     self.queryset = self.get_queryset()
    #
    def get_queryset(self):
        return self.request.user.datasheet_set.all()

    # def get(self, request, format=None):
    #     user = request.user
    #     queryset = user.datasheet_set.all()
    #     sheetmanagers = [SheetManager(sheet) for sheet in datasheets]
    #
    #     sheet_serializer = DataSheetSerializer#(datasheets, many=True)
    #     return Response(sheet_serializer.data)


