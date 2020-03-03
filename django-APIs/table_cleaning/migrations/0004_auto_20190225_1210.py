# Generated by Django 2.1.7 on 2019-02-25 11:10

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('table_cleaning', '0003_claim_chrono'),
    ]

    operations = [
        migrations.CreateModel(
            name='ContractClause',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, default='Clause Name', max_length=1000)),
                ('text', models.CharField(db_index=True, default='Clause Text', max_length=1000)),
            ],
        ),
        migrations.RemoveField(
            model_name='reinsurancecontract',
            name='text',
        ),
        migrations.AddField(
            model_name='contractclause',
            name='contract',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='table_cleaning.ReinsuranceContract'),
        ),
    ]
