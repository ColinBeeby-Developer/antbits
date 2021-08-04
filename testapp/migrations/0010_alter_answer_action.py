# Generated by Django 3.2.5 on 2021-07-28 10:13

from django.db import migrations
import wagtail.core.blocks
import wagtail.core.fields


class Migration(migrations.Migration):

    dependencies = [
        ('testapp', '0009_alter_answer_action'),
    ]

    operations = [
        migrations.AlterField(
            model_name='answer',
            name='action',
            field=wagtail.core.fields.StreamField([('action', wagtail.core.blocks.StructBlock([('operator', wagtail.core.blocks.CharBlock(required=False)), ('type', wagtail.core.blocks.CharBlock()), ('sub_type', wagtail.core.blocks.CharBlock(required=False)), ('value', wagtail.core.blocks.CharBlock())]))]),
        ),
    ]
