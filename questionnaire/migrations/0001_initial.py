# Generated by Django 3.2.5 on 2021-08-03 10:39

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('wagtailcore', '0062_comment_models_and_pagesubscription'),
    ]

    operations = [
        migrations.CreateModel(
            name='Questionnaire',
            fields=[
                ('page_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='wagtailcore.page')),
                ('json_url', models.CharField(max_length=250)),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page',),
        ),
    ]
