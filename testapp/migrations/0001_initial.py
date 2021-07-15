# Generated by Django 3.2.5 on 2021-07-15 15:28

from django.db import migrations, models
import django.db.models.deletion
import modelcluster.fields
import wagtail.core.blocks
import wagtail.core.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('wagtailcore', '0062_comment_models_and_pagesubscription'),
    ]

    operations = [
        migrations.CreateModel(
            name='Answer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('answer_text', models.CharField(max_length=250)),
                ('action', wagtail.core.fields.StreamField([('operator', wagtail.core.blocks.CharBlock(form_classname='full title')), ('type', wagtail.core.blocks.CharBlock()), ('value', wagtail.core.blocks.CharBlock())])),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='QuestionPage',
            fields=[
                ('page_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='wagtailcore.page')),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page',),
        ),
        migrations.CreateModel(
            name='QuestionType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('question_type', models.CharField(max_length=255)),
            ],
            options={
                'verbose_name': 'Question Type',
            },
        ),
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('question_text', models.CharField(max_length=250)),
                ('info_box_title', models.CharField(blank=True, max_length=250)),
                ('info_box_body', wagtail.core.fields.RichTextField(blank=True)),
                ('question_type', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='testapp.questiontype')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='QuestionPageRelatedQuestions',
            fields=[
                ('question_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='testapp.question')),
                ('sort_order', models.IntegerField(blank=True, editable=False, null=True)),
                ('page', modelcluster.fields.ParentalKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='related_questions', to='testapp.questionpage')),
            ],
            options={
                'ordering': ['sort_order'],
                'abstract': False,
            },
            bases=('testapp.question', models.Model),
        ),
        migrations.CreateModel(
            name='QuestionAnswer',
            fields=[
                ('answer_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='testapp.answer')),
                ('sort_order', models.IntegerField(blank=True, editable=False, null=True)),
                ('page', modelcluster.fields.ParentalKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='question_answer', to='testapp.question')),
            ],
            options={
                'ordering': ['sort_order'],
                'abstract': False,
            },
            bases=('testapp.answer', models.Model),
        ),
    ]
