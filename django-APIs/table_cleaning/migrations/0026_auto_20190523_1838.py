# Generated by Django 2.1.1 on 2019-05-23 16:38

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('table_cleaning', '0025_floatkeyval_intkeyval'),
    ]

    operations = [
        migrations.CreateModel(
            name='KeyVal',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(db_index=True, max_length=100)),
                ('tag', models.CharField(choices=[('UN', 'Undefined'), ('EML', 'EML'), ('ETB', 'EML/TSI band'), ('PR', 'Premium income'), ('YR', 'Year'), ('NR', '# of objects'), ('TSI', 'TSI'), ('LO', 'Loss'), ('ID', 'Id'), ('CA', 'Cause'), ('OC', 'Occupancy'), ('SEG', 'Segment'), ('TAG', 'Tag'), ('OT', 'Other')], db_index=True, default='UN', max_length=3)),
                ('xls_type', models.IntegerField(choices=[(0, 'Empty string'), (1, 'String'), (2, 'Float'), (3, 'Excel date'), (4, 'Boolean'), (5, 'Error'), (6, 'Zero float'), (7, 'String'), (8, 'Order')], default=1)),
                ('chrono', models.IntegerField()),
                ('entry', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='table_cleaning.Entry')),
                ('super_data_sheet', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='table_cleaning.DataSheet')),
            ],
        ),
        migrations.RemoveField(
            model_name='floatkeyval',
            name='chrono',
        ),
        migrations.RemoveField(
            model_name='floatkeyval',
            name='entry',
        ),
        migrations.RemoveField(
            model_name='floatkeyval',
            name='id',
        ),
        migrations.RemoveField(
            model_name='floatkeyval',
            name='key',
        ),
        migrations.RemoveField(
            model_name='floatkeyval',
            name='super_data_sheet',
        ),
        migrations.RemoveField(
            model_name='floatkeyval',
            name='tag',
        ),
        migrations.RemoveField(
            model_name='floatkeyval',
            name='xls_type',
        ),
        migrations.RemoveField(
            model_name='intkeyval',
            name='chrono',
        ),
        migrations.RemoveField(
            model_name='intkeyval',
            name='entry',
        ),
        migrations.RemoveField(
            model_name='intkeyval',
            name='id',
        ),
        migrations.RemoveField(
            model_name='intkeyval',
            name='key',
        ),
        migrations.RemoveField(
            model_name='intkeyval',
            name='super_data_sheet',
        ),
        migrations.RemoveField(
            model_name='intkeyval',
            name='tag',
        ),
        migrations.RemoveField(
            model_name='intkeyval',
            name='xls_type',
        ),
        migrations.RemoveField(
            model_name='stringkeyval',
            name='chrono',
        ),
        migrations.RemoveField(
            model_name='stringkeyval',
            name='entry',
        ),
        migrations.RemoveField(
            model_name='stringkeyval',
            name='id',
        ),
        migrations.RemoveField(
            model_name='stringkeyval',
            name='key',
        ),
        migrations.RemoveField(
            model_name='stringkeyval',
            name='super_data_sheet',
        ),
        migrations.RemoveField(
            model_name='stringkeyval',
            name='tag',
        ),
        migrations.RemoveField(
            model_name='stringkeyval',
            name='xls_type',
        ),
        migrations.AddField(
            model_name='floatkeyval',
            name='keyval_ptr',
            field=models.OneToOneField(auto_created=True, default=None, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='table_cleaning.KeyVal'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='intkeyval',
            name='keyval_ptr',
            field=models.OneToOneField(auto_created=True, default=None, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='table_cleaning.KeyVal'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='stringkeyval',
            name='keyval_ptr',
            field=models.OneToOneField(auto_created=True, default=None, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='table_cleaning.KeyVal'),
            preserve_default=False,
        ),
    ]
