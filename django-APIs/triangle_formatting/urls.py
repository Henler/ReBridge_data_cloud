from . import views
from django.urls import path


app_name = 'triangle_formatting'
urlpatterns = [
    path('settings_API', views.FormatSettingsAPI.as_view(), name='format_settings'),
    path('buildoutput_API', views.ConnectDataAPIView.as_view(), name='recieve_data'),
    path('DUMMY_buildoutput_API', views.DUMMY_ConnectDataAPIView.as_view(), name='DUMMY_recieve_data'),
    path('change_dimension_API', views.ChangeDimensionAPIView.as_view(), name='changeDimensionAPI'),
    path('update_API', views.UpdateTablesAPI.as_view(), name='update_tables'),
    path('recive_sheets_and_name_API', views.fileSheetsAndNameAPI.as_view(), name='reciveSheetsAndNameAPI'),
    path('build_data_holder_API', views.buildDataHolderAPI.as_view(), name='buildDataHolderAPI'),
    path('select_dimensions_API', views.selectDimensions.as_view(), name='selectDimensionsAPI'),
]
pass