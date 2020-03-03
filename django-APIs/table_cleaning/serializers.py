from rest_framework.serializers import ModelSerializer

from .models import DataSheet

#Are we still using this?
class DataSheetSerializer(ModelSerializer):

    class Meta:
        model = DataSheet
        fields = ('id', 'sheet_name', 'pub_date')

