# Generated by Django 2.1.1 on 2019-07-04 13:11

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('table_cleaning', '0030_auto_20190703_1323'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='header',
            name='input_triangle',
        ),
        migrations.RemoveField(
            model_name='row',
            name='input_triangle',
        ),
        migrations.DeleteModel(
            name='Header',
        ),
        migrations.DeleteModel(
            name='InputTriangle',
        ),
        migrations.DeleteModel(
            name='Row',
        ),
    ]
