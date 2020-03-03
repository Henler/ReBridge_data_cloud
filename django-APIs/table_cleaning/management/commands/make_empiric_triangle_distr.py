from django.core.management.base import BaseCommand
from data_cloud.distributions.empiric_triangle_distributions import TriangleDistributionMaker




class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        tdm = TriangleDistributionMaker()
        tdm.read_triangles_from_xls()


