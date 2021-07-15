from django.db import models
from django.db.models.fields.related import ForeignKey
from wagtail.admin.edit_handlers import InlinePanel, MultiFieldPanel, FieldPanel, RichTextFieldPanel, StreamFieldPanel
from wagtail.snippets.edit_handlers import SnippetChooserPanel
from wagtail.core.fields import RichTextField, StreamField
from wagtail.core.models import Page, Orderable
from modelcluster.fields import ParentalKey
from wagtail.snippets.models import register_snippet
from modelcluster.models import ClusterableModel
from wagtail.core import blocks


@register_snippet
class QuestionType(models.Model):
    question_type = models.CharField(max_length=255)

    panels = [
        FieldPanel("question_type"), 
    ]

    def __str__(self):
        return self.question_type

    class Meta:
        verbose_name = "Question Type"

## apparently it is not possible to nest inline panels!
# class Action(ClusterableModel):
#     operator = models.CharField(max_length=10)
#     type = models.CharField(max_length=10)
#     value = models.CharField(max_length=20)

#     Panels = [
#         FieldPanel('operator'),
#         FieldPanel('type'),
#         FieldPanel('value')
#     ]


# class AnswerAction(Orderable, Action):
#     page = ParentalKey('testapp.Answer',
#         null=True,
#         on_delete=models.CASCADE,
#         related_name='answer_action')


class Answer(ClusterableModel):
    answer_text = models.CharField(max_length=250)
    # action = StreamField([
    #     ('operator', blocks.CharBlock(form_classname="full title")),
    #     ('type', blocks.CharBlock()),
    #     ('value', blocks.CharBlock()),
    # ])

    action = StreamField([
        ('action', blocks.StructBlock([
            ('operator', blocks.CharBlock()),
            ('type', blocks.CharBlock()),
            ('value', blocks.CharBlock()),
        ]))
    ])
    Panels = [
        FieldPanel('answer_text'),
        #InlinePanel('answer_action', label='Action')
        StreamFieldPanel('action')
    ]


class QuestionAnswer(Orderable, Answer):
    page = ParentalKey('testapp.Question',
        null=True,
        on_delete=models.CASCADE,
        related_name='question_answer')


class Question(ClusterableModel):
    question_text = models.CharField(max_length=250)
    question_type = models.ForeignKey('QuestionType',
        null=True,
        blank=False,
        on_delete=models.SET_NULL,
        related_name="+")
    info_box_title = models.CharField(max_length=250, blank=True)
    info_box_body = RichTextField(blank=True)

    panels = [
        FieldPanel('question_text'),
        SnippetChooserPanel('question_type'),
        
        MultiFieldPanel(
            [
                FieldPanel('info_box_title'),
                RichTextFieldPanel('info_box_body')
            ],
            heading="Info Box",
            classname="collapsible collapsed",
        ),
        InlinePanel('question_answer', label='Answer'),
    ]

class QuestionPageRelatedQuestions(Orderable, Question):
    page = ParentalKey('testapp.QuestionPage', 
                        null=True,
                        on_delete=models.CASCADE, 
                        related_name='related_questions')


class QuestionPage(Page):
    content_panels = Page.content_panels + [
        InlinePanel('related_questions', label="Related Questions"),
    ]