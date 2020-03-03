# Generated by Django 2.1.7 on 2019-02-21 08:07

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('url', models.CharField(db_index=True, max_length=240)),
                ('name', models.CharField(db_index=True, max_length=240)),
            ],
        ),
        migrations.CreateModel(
            name='Claim',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pub_date', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Date of insertion')),
            ],
        ),
        migrations.CreateModel(
            name='ClaimsBook',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('book_name', models.CharField(max_length=200)),
                ('pub_date', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Date of insertion')),
                ('is_aggregate', models.BooleanField(default=False)),
                ('owner', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='KeyVal',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(db_index=True, max_length=240)),
                ('value', models.CharField(db_index=True, max_length=240)),
                ('claim', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='table_cleaning.Claim')),
            ],
        ),
        migrations.CreateModel(
            name='ReinsuranceContract',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.CharField(db_index=True, default='THE LEGAL TEXT', max_length=1000000)),
                ('name', models.CharField(db_index=True, max_length=100)),
                ('owner', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='StopLossContract',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('line', models.IntegerField(default=0)),
                ('contract', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='table_cleaning.ReinsuranceContract')),
            ],
        ),
        migrations.AddField(
            model_name='claim',
            name='claimsBook',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='table_cleaning.ClaimsBook'),
        ),
    ]
