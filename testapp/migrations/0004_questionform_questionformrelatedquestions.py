# Generated by Django 3.2.5 on 2021-07-27 11:35

from django.db import migrations, models
import django.db.models.deletion
import modelcluster.fields
import wagtail.core.fields


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0062_comment_models_and_pagesubscription'),
        ('testapp', '0003_questionpage_introduction_text'),
    ]

    operations = [
        migrations.CreateModel(
            name='QuestionForm',
            fields=[
                ('page_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='wagtailcore.page')),
                ('introduction_text', wagtail.core.fields.RichTextField(blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page',),
        ),
        migrations.CreateModel(
            name='QuestionFormRelatedQuestions',
            fields=[
                ('question_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='testapp.question')),
                ('sort_order', models.IntegerField(blank=True, editable=False, null=True)),
                ('page', modelcluster.fields.ParentalKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='related_questions', to='testapp.questionform')),
            ],
            options={
                'ordering': ['sort_order'],
                'abstract': False,
            },
            bases=('testapp.question', models.Model),
        ),
    ]
