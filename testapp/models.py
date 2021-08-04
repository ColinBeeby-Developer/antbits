from django.db import models
from django.db.models.fields.related import ForeignKey
from wagtail.admin.edit_handlers import InlinePanel, MultiFieldPanel, FieldPanel, RichTextFieldPanel, StreamFieldPanel, PageChooserPanel
from wagtail.snippets.edit_handlers import SnippetChooserPanel
from wagtail.core.fields import RichTextField, StreamField
from wagtail.core.models import Page, Orderable
from modelcluster.fields import ParentalKey
from wagtail.snippets.models import register_snippet
from modelcluster.models import ClusterableModel
from wagtail.core import blocks
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from wagtail.contrib.forms.models import AbstractForm, AbstractFormField
from django.shortcuts import render, redirect



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

@register_snippet
class InfoBox(models.Model):
    info_box_id = models.CharField(max_length=256)
    body = models.CharField(max_length=2048)
    name = models.CharField(max_length=256)

    panels = [
        FieldPanel("info_box_id"),
        FieldPanel("body"),
        FieldPanel("name"),
    ]

    def __str__(self):
        return self.name

    class Meta:
        verbose_name="Info Box"

class Answer(ClusterableModel):
    answer_text = models.CharField(max_length=250)
    action = StreamField([
        ('action', blocks.StructBlock([
            ('operator', blocks.CharBlock(required=False)),
            ('type', blocks.CharBlock()),
            ('sub_type', blocks.CharBlock(required=False)),
            ('value', blocks.CharBlock()),
        ]))
    ])

    Panels = [
        FieldPanel('answer_text'),
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
    info_box_title = models.CharField(max_length=250, blank=True) # This is not required now
    info_box_body = RichTextField(blank=True) # This is not required now
    info_box = models.ForeignKey('InfoBox',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+")

    panels = [
        FieldPanel('question_text'),
        FieldPanel('question_type'),
        FieldPanel('info_box'),
        
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


class QuestionFormRelatedQuestions(Orderable, Question):
    page = ParentalKey('testapp.QuestionForm',
                        null=True,
                        on_delete=models.CASCADE,
                        related_name='related_questions')

class QuestionForm(AbstractForm):
    introduction_text = RichTextField(blank=True)
    results_page = models.ForeignKey(
        'wagtailcore.page',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )
    content_panels = AbstractForm.content_panels + [
        FieldPanel('introduction_text', classname="full"),
        InlinePanel('related_questions', label="Related Questions"),
        PageChooserPanel('results_page'),
    ]


    def serve(self, request, *args, **kwargs):
        """
        Implements a simple multi-step form.
        """
        session_key_data = 'form_data-%s' % self.pk
        is_last_step = False
        step_number = request.GET.get('p', 0)
        total_questions = 0

        if step_number == 0: # This is a bit of a botch to get the intro to display as first page - might be better as a foreign key page?
            return self.render_intro_page(request)

        paginator = Paginator(self.get_questions(), per_page=1)
        total_questions = paginator.num_pages
        try:
            step = paginator.page(step_number)
        except PageNotAnInteger:
            step = paginator.page(1)
        except EmptyPage:
            step = paginator.page(paginator.num_pages)
            is_last_step = True

        if request.method == 'POST' and int(step_number) > 1:
            # The first step will be submitted with step_number == 2,
            # so we need to get a form from previous step
            # Edge case - submission of the last step
            prev_step = step if is_last_step else paginator.page(step.previous_page_number())

            # Create a form only for submitted step
            prev_form = self.create_form_for_step(prev_step)
            if prev_form.is_valid():
                # If data for step is valid, update the session
                form_data = request.session.get(session_key_data, {})
                cleaned_data = prev_form.get_cleaned_data(request.POST.get('answer'))
                form_data[prev_step.number] = cleaned_data
                request.session[session_key_data] = form_data

                if prev_step.has_next():
                    # Create a new form for a following step, if the following step is present
                    form = self.create_form_for_step(step)
                else:
                    return self.render_landing_page(request, None, *args, **kwargs)
            else:
                # If data for step is invalid
                # we will need to display form again with errors,
                # so restore previous state.
                form = prev_form
                step = prev_step
        else:
            # Create empty form for non-POST requests
            form = self.create_form_for_step(step)


        context = self.get_context(request)
        context['form'] = form
        context['fields_step'] = step
        context['total_questions'] = total_questions
        return render(
            request,
            self.template,
            context
        )

    def create_form_for_step(self, step):
        question_and_answers = QuestionAndAnswersData()
        question_and_answers.question_text = step.object_list[0].question_text
        question_and_answers.question_type = step.object_list[0].question_type.question_type
        if step.object_list[0].info_box:
            question_and_answers.info_box_name = step.object_list[0].info_box.name
            question_and_answers.info_box_body = step.object_list[0].info_box.body
        
        for question_answer in step.object_list[0].question_answer.all():
            answer = AnswerData()
            answer.answer_text = question_answer.answer_text
            answer.answer_id = question_answer.id
            for answer_action in question_answer.action:
                action = Action()
                action.operator = answer_action.value.get('operator', '')
                action.type = answer_action.value['type']
                action.value = answer_action.value['value']
                action.sub_type = answer_action.value.get('sub_type', '')
                answer.actions.append(action)
            question_and_answers.answers.append(answer)

        return question_and_answers

    def render_intro_page(self, request):
        context = self.get_context(request)
        context['fields_step'] = {'number': 0}
        return render(
            request,
            self.template,
            context
        )
    
    def get_questions(self):
        return self.related_questions.all()

    def render_landing_page(self, request, form_submission, *args, **kwargs):
        if self.results_page:
            url = self.results_page.url
            # if form_submission:
            url += '?id=%s' % 'form_data-%s' % self.pk
            return redirect(url, permanent=False)
        return super().render_landing_page(request, form_submission=form_submission, *args, **kwargs)

class QuestionAndAnswersData(object):
    _question_text=''
    _question_type=''
    _info_box_name=''
    _info_box_body=''
    _answers = []

    def __init__(self):
        self._answers = []

    def is_valid(self):
        # TODO - need to add some validation here
        # if question_type is single select, then one option must be selected
        return True

    @property
    def question_text(self):
        return self._question_text
    
    @question_text.setter
    def question_text(self, value):
        self._question_text = value

    @property
    def question_type(self):
        return self._question_type

    @question_type.setter
    def question_type(self, value):
        self._question_type = value

    @property
    def answers(self):
        return self._answers

    @answers.setter
    def answers(self, value):
        self._answers = value

    @property
    def info_box_name(self):
        return self._info_box_name

    @info_box_name.setter
    def info_box_name(self, value):
        self._info_box_name = value
    
    @property
    def info_box_body(self):
        return self._info_box_body

    @info_box_body.setter
    def info_box_body(self, value):
        self._info_box_body=value

    def get_cleaned_data(self, answer_text):
        actions=[]
        for answer in self._answers:
            if answer.answer_text == answer_text:
                for action in answer.actions:
                    actions.append({'operator':action.operator, 'type':action.type, 'value':action.value, 'sub_type':action.sub_type})
        return actions

class AnswerData(object):
    _answer_text=''
    _answer_id=''
    _actions = []

    def __init__(self):
        self._actions = []

    @property
    def answer_text(self):
        return self._answer_text

    @answer_text.setter
    def answer_text(self, value):
        self._answer_text = value

    @property
    def answer_id(self):
        return self._answer_id

    @answer_id.setter
    def answer_id(self, value):
        self._answer_id = value

    @property
    def actions(self):
        return self._actions

    @actions.setter
    def actions(self, value):
        self._actions = value

class Action(object):
    _operator=''
    _type=''
    _value=''
    _sub_type=''

    @property
    def operator(self):
        return self._operator

    @operator.setter
    def operator(self, value):
        self._operator = value

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, value):
        self._type = value

    @property
    def value(self):
        return self._value
    
    @value.setter
    def value(self, value_value):
        self._value = value_value

    @property
    def sub_type(self):
        return self._sub_type

    @sub_type.setter
    def sub_type(self, value):
        self._sub_type = value
