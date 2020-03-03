from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.contrib.auth.models import Group


class Command(BaseCommand):

    def handle(self, *args, **options):
        if not User.objects.filter(username="admin").exists():
            admin = User.objects.get_or_create_superuser("admin", "admin@admin.com", "ghetto_body_buddy")
            new_group, created = Group.objects.get_or_create(name='reinsurance')
            new_group.user_set.add(admin)
            new_group, created = Group.objects.get_or_create(name='insurance')
            new_group.user_set.add(admin)
            new_group, created = Group.objects.get_or_create(name='broker')
            new_group.user_set.add(admin)