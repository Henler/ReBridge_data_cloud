import json
import os
import shutil
import jsonpickle
import pickle
import pandas as pd
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect

# Create your views here.
from django.views import generic
from rest_framework.authentication import BasicAuthentication
from rest_framework.response import Response
from rest_framework.views import APIView

from python_back_end.exceptions import DataHolderException
from python_back_end.triangle_formatting.triangle_pipeline import TrianglePipeline
from python_back_end.triangle_formatting.triangle_utils import InputMatcher
from python_back_end.utilities.sheet_io import SheetWriter
from python_back_end.utilities.state_handling import DataHolder
from python_back_end.utilities.sheet_io import ExcelLoader
from python_back_end.program_settings import PROGRAM_DIRECTORIES as pdir
from python_back_end.program_settings import PROGRAM_STRINGS as ps
from python_back_end.triangle_formatting.triangle_rendering import RowParser
from python_back_end.triangle_formatting.triangle_templater import TriangleTemplater
from rest_framework.authentication import SessionAuthentication
from rest_framework.parsers import FileUploadParser, MultiPartParser
from django.core.files.uploadedfile import TemporaryUploadedFile, InMemoryUploadedFile
import tempfile
import xlrd


class CsrfExemptSessionAuthentication(SessionAuthentication):

    def enforce_csrf(self, request):
        return  # To not perform the csrf check previously happening


class DUMMY_ConnectDataAPIView(APIView):
    #Skips CSRF verification
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)

    def post(self, request):

        with open("test_file_henrik", "rb") as f:
            response_data = pickle.load(f)

        return Response({'data': response_data})

class ChangeDimensionAPIView(APIView):
    #Skips CSRF verification
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)

    def post(self, request):
        # Need to post - str_data_holder, output triangles (templates)

        str_data_holder = request.data.get('str_data_holder')
        data_holder = DataHolder.decode(str_data_holder)


        response_data = {}

        if data_holder is None:
            raise ValueError("No data holder found")
        elif data_holder.n == 0:
            raise ValueError("No sheets in data holder")
        
        #Recieve triangle formats
        user_defined_triangles = request.data.get('templates')

        try:
            #DataHolder manipulation
            data_holder, group_ids, sheet_names = RowParser.set_card_ids(user_defined_triangles, data_holder)
            user_defined_triangles = InputMatcher.match_triangles_to_output(user_defined_triangles, data_holder)
            user_defined_triangles = RowParser.parse_output_from_triangle_forms(user_defined_triangles, data_holder)
        except DataHolderException as err:
            data = {}
            data['message'] = err.message
            data['dh'] = err.dh
            return Response({'response_error': data})

        #SheetWriter.trngs_to_existing_excel(user_defined_triangles, pdir.TEMP_DIR + ps.OUTPUT_NAME + filename)

        response_data["group_ids"] = group_ids 
        response_data['output_triangles'] = user_defined_triangles
        response_data["unit_triangles"] = ChangeDimensionAPIView.make_unit_triangle_list(data_holder)

        return Response({'data': response_data})

    @staticmethod
    def make_unit_triangle_list(data_holder):
        unit_triangles = []
    # Needed fields, .card_id, .roles, orig_sheet_name, .name, .df_data.columns.values, df_data.values

        for ds in data_holder:
            triangle = {}
            triangle["rows"] = ds.df_data.values.tolist()
            triangle["headers"] = ds.df_data.columns.values.tolist()
            triangle["name"] = ds.name
            triangle["orig_sheet_name"] = ds.orig_sheet_name
            triangle["roles"] = ds.roles
            triangle["card_id"] = ds.card_id
            triangle["id"] = ds.id
            triangle["fit_for_output"] = ds.fit_for_output
            unit_triangles.append(triangle)
        return unit_triangles




class ConnectDataAPIView(APIView):
    #Skips CSRF verification
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)

    def post(self, request):

        #Recieve name of file
        filename = request.data.get('fileName')
        # Build data holder
        sr_list = jsonpickle.decode(request.data['sr_list'])
        selected_sheets = request.data['selected_sheets']

        data_holder = DataHolder(filename)

        for sr in sr_list:
            if sr.sheet_name in selected_sheets:
                data_holder.add_sheet(sr.sheet_name, pd.DataFrame(columns=sr.headers, data=sr.row_vals),
                                  pd.DataFrame(columns=sr.headers, data=sr.xls_types),
                                  orig_sheet_name=sr.sheet_name)

        response_data = {}
        #dump this shiiiit
        #data_holder.to_pickle_file(pdir.TEMP_DIR + "from_views.pickle")
        if data_holder is None:
            raise ValueError("No data holder found")
        elif data_holder.n == 0:
            raise ValueError("No sheets in data holder")
        
        #Recieve triangle formats
        triangles = request.data.get('triangles')
        user_defined_triangles = triangles['templates']
        outputFormats = triangles['output_formats']
        n_outputs = triangles['number_of_outputs']
        input_format = triangles['inputFormat']
        tr_type = user_defined_triangles[0]['type']
        # if tr_type == "single":
        #     n_outputs = len(user_defined_triangles)
        # else:
        #     n_outputs = int(len(user_defined_triangles)/2)
        try:
            if input_format[0] == 'triangle':
                #print(tr_type, n_outputs)
                data_holder_dict, data_holder = TrianglePipeline.triangle_pipeline_dh(data_holder, tri_type=tr_type, n_outputs=n_outputs)
            else:
                data_holder_dict, data_holder = TrianglePipeline.table_triangle_pipeline_dh(data_holder)
            #DataHolder manipulation
            data_holder, group_ids, sheet_names = RowParser.set_card_ids(user_defined_triangles, data_holder)
            user_defined_triangles = InputMatcher.match_triangles_to_output(user_defined_triangles, data_holder)
            user_defined_triangles = RowParser.parse_output_from_triangle_forms(user_defined_triangles, data_holder)
        except DataHolderException as err:
            data = {}
            data['message'] = err.message
            data['dh'] = err.dh
            return Response({'response_error': data})

        SheetWriter.trngs_to_existing_excel(user_defined_triangles, pdir.TEMP_DIR + ps.OUTPUT_NAME + filename)


        #Unsure if all neded
        response_data["group_ids"] = group_ids 
        response_data['output_triangles'] = user_defined_triangles
        #Building list for initial rendering


        response_data["unit_triangles"] = ConnectDataAPIView.make_unit_triangle_list(data_holder)
        response_data["str_data_holder"] = data_holder.encode()
        if len(data_holder_dict) > 1:
            response_data["str_data_holder_dict"] = {key: val.encode() for key, val in data_holder_dict.items()}
        else:
            response_data["str_data_holder_dict"] = {data_holder.name: response_data["str_data_holder"]}

        return Response({'data': response_data})

    @staticmethod
    def make_unit_triangle_list(data_holder):
        unit_triangles = []
    # Needed fields, .card_id, .roles, orig_sheet_name, .name, .df_data.columns.values, df_data.values

        for ds in data_holder:
            triangle = {}
            triangle["rows"] = ds.df_data.values.tolist()
            triangle["headers"] = ds.df_data.columns.values.tolist()
            triangle["name"] = ds.name
            triangle["orig_sheet_name"] = ds.orig_sheet_name
            triangle["roles"] = ds.roles
            triangle["card_id"] = ds.card_id
            triangle["id"] = ds.id
            triangle["fit_for_output"] = ds.fit_for_output
            unit_triangles.append(triangle)
        return unit_triangles


class UpdateTablesAPI(APIView):
    #Skips CSRF verification
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)

    def post(self, request):
        user_defined_triangles = request.data.get("output")
        input_json = request.data.get("input")
        dh = DataHolder.decode(input_json)
        #dh, group_ids, sheet_names = RowParser.set_card_ids(user_defined_triangles, dh)
        change = request.data.get("change")
        filename = request.data.get("filename")
        # Update connection with the change variable
        RowParser.make_changes(dh, user_defined_triangles, change)
        user_defined_triangles = RowParser.parse_output_from_triangle_forms(user_defined_triangles, dh)
        SheetWriter.trngs_to_existing_excel(user_defined_triangles, pdir.TEMP_DIR + ps.OUTPUT_NAME + filename)
        return Response({'output': user_defined_triangles})


class FormatSettingsAPI(APIView):
    #Skips CSRF verification
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)

    def post(self, request):

        table_type = request.data.get("type", "single")
        nmbr_outputs = request.data.get("nmbr_outputs", "0")

        # outputFormats ["Claims", "Premiums"]
        outputFormats = request.data['outputFormats']

        # Cath error if outputformats is empty
        if (len(outputFormats) == 0):
            outputFormats = ['Premiums', 'Claims']

        try:
            nmbr_of_output_triangles = int(nmbr_outputs)
        except:
            nmbr_of_output_triangles = 0


        triangle_template = []
        if table_type == "single":
            triangle_template = TriangleTemplater.get_single_loss_triangle_template()
        elif table_type == "aggregate":
            triangle_template = TriangleTemplater.get_aggregate_loss_triangle_template(outputFormats)

        triangles = {}
        triangles['templates'] = TriangleTemplater.create_triangle_template_with_group_ids(triangle_template, nmbr_of_output_triangles)
        triangles['output_formats'] = outputFormats
        triangles['number_of_outputs'] = nmbr_outputs
        return Response(triangles, status=200)


class selectDimensions(APIView):
    #Skips CSRF verification
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)

    def post(self, request):

        # Probably want to send output, input and dimensions 
        # user_defined_triangles = request.data.get("output")
        # input_json = request.data.get("input")
        # dh = DataHolder.decode(input_json)
        # change = request.data.get("dimensions")

        # Build loop to update triangles 
        
        # user_defined_triangles = RowParser.parse_output_from_triangle_forms(user_defined_triangles, dh)
        # SheetWriter.trngs_to_excel(user_defined_triangles)
        return Response('["Dimension 1", "Dimension 2", "Dimension 3", "Dimension 4", "Dimension 5", "Dimension 6", "Dimension 7"]', status=200)

class fileSheetsAndNameAPI(APIView):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
    parser_classes = [MultiPartParser]

    def post(self, request):
        response_data = {}
        file_obj = request.data['file']

        try:
            nfp = tempfile.NamedTemporaryFile(suffix="." + file_obj.name.split(".")[-1], delete=False)
            nfp.write(file_obj.read())
            sr_list, dummy = ExcelLoader.load_excel(nfp.name)
            file_name = nfp.name
            nfp.close()

            shutil.copy(file_name, pdir.TEMP_DIR + ps.OUTPUT_NAME + file_obj.name)
        except:
            print("An exception occurred")  

        response_data["dhName"] = file_obj.name
        response_data["sr_list"] = jsonpickle.encode(sr_list)

        return Response(response_data, status=200)


class buildDataHolderAPI(APIView):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)

    def post(self, request):
        sr_list = jsonpickle.decode(request.data['sr_list'])
        dhName = request.data['dhName']
        selected_sheets = request.data['selected_sheets']

        data_holder = DataHolder(dhName)

        for sr in sr_list:
            if sr.sheet_name in selected_sheets:
                data_holder.add_sheet(sr.sheet_name, pd.DataFrame(columns=sr.headers, data=sr.row_vals),
                                  pd.DataFrame(columns=sr.headers, data=sr.xls_types),
                                  orig_sheet_name=sr.sheet_name)

        encoded = data_holder.encode()

        return Response(encoded, status=200)
