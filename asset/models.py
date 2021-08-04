from django.db import models

from wagtail.core.models import Page
from wagtail.core.fields import RichTextField
# from wagtail.admin.edit_handlers import FieldPanel
from wagtail.search import index
import requests
from wagtail.contrib.forms.models import AbstractForm, AbstractFormField
from modelcluster.fields import ParentalKey
from wagtail.admin.edit_handlers import (
    FieldPanel, FieldRowPanel,
    InlinePanel, MultiFieldPanel,
    PageChooserPanel
)
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import render, redirect
from django.forms import widgets

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

class AssetStartPage(Page):
    intro = models.CharField(max_length=250)
    important_text = models.CharField(max_length=250)
    quiz_start_url = models.CharField(max_length=250)
    quiz_start_text = models.CharField(max_length=250)
    
    search_fields = Page.search_fields + [
        index.SearchField('intro'),
    ]

    content_panels = Page.content_panels + [
        FieldPanel('intro'),
        FieldPanel('important_text'),
        FieldPanel('quiz_start_url'),
        FieldPanel('quiz_start_text'),
    ]

# https://docs.wagtail.io/en/stable/reference/contrib/forms/customisation.html

class FormField(AbstractFormField):
    page = ParentalKey('FormPage', on_delete=models.CASCADE, related_name='form_fields')

class FormPage(AbstractForm):
    intro = RichTextField(blank=True)
    thank_you_text = RichTextField(blank=True)

    results_page = models.ForeignKey(
        'wagtailcore.page',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )

    content_panels = AbstractForm.content_panels + [
        FieldPanel('intro', classname="full"),
        InlinePanel('form_fields', label="Form fields"),
        FieldPanel('thank_you_text', classname="full"),
        PageChooserPanel('results_page')
    ]

    def get_form_class_for_step(self, step):
        return self.form_builder(step.object_list).get_form_class()

    def serve(self, request, *args, **kwargs):
        """
        Implements a simple multi-step form.

        Stores each step into a session.
        When the last step was submitted correctly, saves whole form into a DB.
        """

        session_key_data = 'form_data-%s' % self.pk
        is_last_step = False
        step_number = request.GET.get('p', 0)
        total_questions = 0

        if step_number == 0: # This is a bit of a botch to get the intro to display as first page - might be better as a foreign key page?
            return self.render_intro_page(request)

        paginator = Paginator(self.get_form_fields(), per_page=1)
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
            prev_form_class = self.get_form_class_for_step(prev_step)
            prev_form = prev_form_class(request.POST, page=self, user=request.user)
            if prev_form.is_valid():
                # If data for step is valid, update the session
                form_data = request.session.get(session_key_data, {})
                form_data.update(prev_form.cleaned_data)
                request.session[session_key_data] = form_data

                if prev_step.has_next():
                    # Create a new form for a following step, if the following step is present
                    form_class = self.get_form_class_for_step(step)
                    form = form_class(page=self, user=request.user)
                else:
                    # If there is no next step, create form for all fields
                    form = self.get_form(
                        request.session[session_key_data],
                        page=self, user=request.user
                    )

                    if form.is_valid():
                        # Perform validation again for whole form.
                        # After successful validation, save data into DB,
                        # and remove from the session.
                        form_submission = self.process_form_submission(form)
                        # del request.session[session_key_data]
                        # render the landing page
                        return self.render_landing_page(request, form_submission, *args, **kwargs)
            else:
                # If data for step is invalid
                # we will need to display form again with errors,
                # so restore previous state.
                form = prev_form
                step = prev_step
        else:
            # Create empty form for non-POST requests
            form_class = self.get_form_class_for_step(step)
            form = form_class(page=self, user=request.user)

        context = self.get_context(request)
        context['form'] = form
        context['fields_step'] = step
        context['total_questions'] = total_questions
        return render(
            request,
            self.template,
            context
        )

    def render_intro_page(self, request):
        context = self.get_context(request)
        context['fields_step'] = {'number': 0}
        return render(
            request,
            self.template,
            context
        )

    def get_form_fields(self):
        return self.form_fields.all()

    def render_landing_page(self, request, form_submission, *args, **kwargs):
        if self.results_page:
            url = self.results_page.url
            if form_submission:
                url += '?id=%s' % 'form_data-%s' % self.pk
            return redirect(url, permanent=False)
        return super().render_landing_page(request, form_submission=form_submission, *args, **kwargs)

class ResultsPage(Page):
    intro = RichTextField(blank=True)

    content_panels = AbstractForm.content_panels + [
        FieldPanel('intro', classname="full"),
    ]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        session_key_data = request.GET.get('id')
        form_data = request.session.get(session_key_data, {})
        del request.session[session_key_data]

        scores = self.calculate_scores(form_data)

        data = requests.get('https://assets.nhs.uk/tools/self-assessments/packages/as_44/data.json').json()

        qvars = data.get('qvars')
        result_sections = ['points']
        for qvar in data.get('qvars', []):
            result_sections.append(qvar)

        context['result_sections'] = []
        
        for result_section in result_sections:
            result_details = {}
            result_details['result_points'] = scores.get(result_section, 0)

            results = []
            points = int(scores.get(result_section, 0))
            for result in data.get('results', []):
                if result_section == 'points' and result.get('type') == 'points triggered result':
                        if int(result.get('p1', "-1")) <= points and int(result.get('p2', '-1')) >= points:
                            results.append(result.get('text'))
                elif result.get('type') == 'variable triggered result' and result.get('p3') == result_section:
                    if int(result.get('p1', '-1')) <= points and int(result.get('p2', '-1')) >= points:
                        results.append(result.get('text'))
            result_details['results'] = results

            result_items = []
            result_section_items = scores.get('results', {}).get(result_section, [])
            for result_section_item in result_section_items:
                for data_result_item in data.get('result_items', []):
                    if data_result_item.get('id') == result_section_item:
                        result_items.append(data_result_item.get('text'))
            result_details['result_items'] = result_items

            progress_bars = []
            for result in data.get('results', []):
                if result.get('type') == 'progress bar' and result.get('p3').lower() == result_section.lower():
                    progress_bars.append({'min':result.get('p1'),
                    'max': result.get('p2'),
                    'text': result.get('text')
                    })
            result_details['progress_bars'] = progress_bars

            context['result_sections'].append(result_details)


        # text that is always displayed
        result_text = []
        for result in data.get('results'):
            if result.get('type') == 'text':
                result_text = context.get('result_text', [])        
                result_text.append(result.get('text'))
        context['result_text'] = result_text                
                
        # Do this just once for all parts
        link_items = []
        for link_item in scores.get('links', []):
            for data_link_item in data.get('link_items', []):
                if data_link_item.get('id') == link_item:
                    link_items.append('{}~{}'.format(data_link_item.get('text'), data_link_item.get('link_url')))
        context['link_items'] = link_items

        return context

    def calculate_scores(self, form_data):
        scores = {}
        
        for answer in form_data:
            for action in form_data[answer]:
                self.process_action(action, scores)
          
        return scores

    def process_action(self, action, scores):
        valid_operations = {'points': self.points,
                            'result': self.result,
                            'link': self.link,
                            'set variable': self.set_variable,
                            'unknown': self.unknown_type}
        try:
            valid_operations[action.get('type', 'unknown')](action['operator'], action.get('sub_type'), action['value'], scores)
        except:
            # TODO - need to do something for an invalid operations
            pass

    def points(self, operator, sub_type_name, value, scores):
        if operator == '+':
            current_score = scores.get('points', 0)
            current_score += int(value)
            scores['points'] = current_score

    def result(self, operator, sub_type_name, value, scores):
        if not sub_type_name:
            sub_type_name = 'points'
        results = scores.get('results', {})
        current_results = results.get(sub_type_name, [])
        current_results.append(value)
        results[sub_type_name] = current_results
        scores['results'] = results
    
    def link(self, operator, sub_type_name, value, scores):
        current_links = scores.get('links', [])
        current_links.append(value)
        scores['links'] = current_links


    def set_variable(self, operator, sub_type_name, value, scores):
        if operator == '+':
            current_variable_value = scores.get(sub_type_name, 0)
            current_variable_value += int(value)
            scores[sub_type_name] = current_variable_value

    def unknown_type(self, operator, sub_type_name, value, scores):
        # TODO decide what we need to do for an unknown action type
        pass