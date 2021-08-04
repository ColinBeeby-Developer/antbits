# Generated by Django 3.2.5 on 2021-07-28 12:57

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('testapp', '0010_alter_answer_action'),
    ]

    operations = [
        migrations.CreateModel(
            name='InfoBox',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('info_box_id', models.CharField(max_length=256)),
                ('body', models.CharField(max_length=2048)),
                ('name', models.CharField(max_length=256)),
            ],
            options={
                'verbose_name': 'Info Box',
            },
        ),
        migrations.AddField(
            model_name='question',
            name='info_box',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='testapp.infobox'),
        ),
    ]
