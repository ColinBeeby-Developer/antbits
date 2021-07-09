from django.db import models

from wagtail.core.models import Page
from wagtail.core.fields import RichTextField
from wagtail.admin.edit_handlers import FieldPanel
from wagtail.search import index
import requests


class AssetIndexPage(Page):
    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel('intro', classname="full")
    ]

class AssetPage(Page):
    intro = models.CharField(max_length=250)

    search_fields = Page.search_fields + [
        index.SearchField('intro'),
    ]

    content_panels = Page.content_panels + [
        FieldPanel('intro'),
    ]

    def get_context(self, request):
        context = super().get_context(request)

        # Get the json which contains the questions
        response = requests.get('https://assets.nhs.uk/tools/self-assessments/packages/as_44/data.json')
        context['config'] = response.json().get('config')
        context['questions'] = response.json().get('questions')
        return context
