from django.core.management.base import BaseCommand
from data_cloud.models import ClaimsBook, Category
from data_cloud.data_cloud_utilities import SubStringer
from django.contrib.auth.models import User
import time



class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        corporate = User.objects.all().get(username="Corporate")
        reinsurer = User.objects.all().get(username="Reinsurer")
        chewbacca = User.objects.all().get(username="chewbacca")


        ClaimsBook.objects.all().delete()


