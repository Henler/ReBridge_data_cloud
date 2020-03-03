from django.urls import path
from django.conf.urls import include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import routers

from . import views

router = routers.DefaultRouter()
router.register(r'api/data_sheets', views.ChartData, basename="datasheet")

app_name = 'table_cleaning'
urlpatterns = [
    path('tables', views.TableView.as_view(), name='tables'),
    path('data_cleaning_table', views.DataCleaningTableView.as_view(), name='data_cleaning_table'),
    path('<int:pk>/', views.TableDetailView.as_view(), name='book_detail'),
    path('charts/', views.ChartsView.as_view(), name='charts'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('customer/', views.CustomerView.as_view(), name='customer'),
    path('messages/', views.MessageView.as_view(), name='messages'),
    path('upload_data', views.NewExposureView.as_view(), name='new_exposure'),
    #path('clean_data', views.CleanDataView.as_view(), name='clean_data'),
    path('tag_data', views.TagDataView.as_view(), name='tag_data'),
    path('analyze_data', views.AnalyzeDataView.as_view(), name='analyze_data'),
    #path('api/', include(router.urls)),
    #path('api/data', include('rest_framework.urls'), name='APIdata')
    #path('api/sheetmanager/data', views.ChartData.as_view(), name='sheetmanager_API'),
    #path('message_log', views.NewTreaty2View.log),
]
for pattern in router.urls:
    urlpatterns.append(pattern)
pass