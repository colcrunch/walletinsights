# Generated by Django 4.0.10 on 2023-11-08 21:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('walletinsights', '0003_remove_walletdivision_division_division_name_idx_and_more'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='walletjournalentry',
            index=models.Index(fields=['division', 'entry_id'], name='division_entry_idx'),
        ),
    ]
