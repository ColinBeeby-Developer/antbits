import requests
from django.db import models
from wagtail.admin.edit_handlers import FieldPanel
from wagtail.core.models import Page


class Questionnaire(Page):
    """ Display a questionnaire based on some acquired JSON """
    json_url = models.CharField(max_length=250)

    content_panels = Page.content_panels + [
        FieldPanel('json_url', classname="full")
    ]

    def get_context(self, request):
        context = super().get_context(request)
        next_step_number = int(request.GET.get('p', 0))
        current_step_number = next_step_number - 1
        session_key_data = 'form_data-%s' % self.pk

        session_data = request.session.get(session_key_data, {})

        self.get_data(request, session_data, session_key_data)

        if request.method == 'POST' and next_step_number > 0:
            posted_answer = request.POST.getlist('answer')
            session_data[current_step_number] = posted_answer
            request.session[session_key_data] = session_data

        context['question_number'] = next_step_number
        context['total_questions'] = len(session_data.get('data', {}).get('questions', []))
        context['questionnaire_elements'] = self.get_questionnaire_elements(next_step_number, session_data, current_step_number)
        context['footer_elements'] = self.get_footer_elements(current_step_number, session_data.get('data', {}).get('config'))
        context['next_step'] = next_step_number + 1
        context['prev_step'] = current_step_number

        return context

    def get_data(self, request, session_data, session_key_data):
        """ 
        Get the JSON data. 
        If it is already in the session, get it from there, 
        else download it and add to cache.
        """
        if session_data.get('data'):
            data = session_data['data']
        else:
            data = requests.get(self.json_url).json()
            session_data['data'] = data
            request.session[session_key_data] = session_data
       
    @classmethod
    def get_questionnaire_elements(cls, next_step_number, session_data, current_step_number):
        questionnaire_elements = ''
        data = session_data.get('data', {})
        if next_step_number == 0:
            questionnaire_elements = cls.create_intro(data)
        elif next_step_number > len(data['questions']):
            questionnaire_elements = cls.create_result(data, session_data)
        else:
            questionnaire_elements = cls.create_question(data, current_step_number)

        return questionnaire_elements

    @staticmethod
    def get_footer_elements(current_step_number, config_data):
        footer_elements = ''
        if current_step_number == -1:
            if config_data.get('intro_foot_title'):
                footer_elements = '<div><details style="display:inline;"><summary>{}</summary>{}</details></div>'.format(config_data.get('intro_foot_title'), config_data.get('intro_foot'))
        
        return footer_elements

    @staticmethod
    def create_intro(data):
        """ Create the markup for the introduction page of the quesionnaire """
        elements = '<h1>{}</h1>'.format(data['config']['title'])
        elements += '<h2>{}</h2>'.format(data['config']['intro_title'])
        elements += data['config']['intro_copy']

        return elements

    @classmethod
    def create_question(cls, data, question_number):
        """ Create the markup for a question """
        question = data['questions'][question_number]
        elements = '<div class="nhsuk-form-group">'
        elements += '<fieldset class="nhsuk-fieldset">'
        elements += '<legend class="nhsuk-fieldset__legend nhsuk-fieldset__legend--l">'
        elements += '<h1 class="nhsuk-fieldset__heading">'
        elements += question['body']
        elements += '</h1>'
        elements += '</legend>'
        if question['info_box']:
            elements += cls.create_info_box(data, question['info_box'])
        if question['type'] == 'single select':
            elements += cls.create_single_select(question)
        elif question['type'] == 'multiple select':
            elements += cls.create_multi_select(question)
        elements += '</fieldset>'
        elements += '</div>'
        return elements

    @staticmethod
    def create_single_select(question):
        """ Create the markup for a single select question """
        elements = '<div class="nhsuk-radios">'
        answer_index = 0
        for answer in question['answers']:
            elements += '<div class="nhsuk-radios__item">'
            elements += '<input class="nhsuk-radios__input" type="radio" name="answer" value="{}" required id="radio_{}">'.format(answer['body'], answer_index)
            elements += '<label class="nhsuk-label nhsuk-radios__label" for="radio_{}">{}</label>'.format(answer_index, answer['body'])
            elements += '</div>'
            answer_index += 1
        elements += '</div>'
        return elements

    @staticmethod
    def create_multi_select(question):
        """ Create the markup for a multiple select question """
        elements = '<div class="nhsuk-checkboxes">'
        answer_index = 0
        for answer in question['answers']:
            elements += '<div class="nhsuk-checkboxes__item">'
            elements += '<input class="nhsuk-checkboxes__input" type="checkbox" name="answer" value="{}" id="checkbox_{}">'.format(answer['body'], answer_index)
            elements += '<label class="nhsuk-label nhsuk-checkboxes__label" for="checkbox_{}">{}</label>'.format(answer_index, answer['body'])
            elements += '</div>'
            answer_index += 1
        elements += "</div>"
        return elements

    @classmethod
    def create_result(cls, data, results_data):
        """ Create the markup for the result page """
        results = cls.calculate_results(data, results_data)
        elements = ''
        index = 0
        for result in data['results']:
            if result['type'] == 'progress bar':
                elements += cls.add_progress_bar(result, results, index)
            elif result['type'] == 'points triggered result':
                elements += cls.add_points_triggered_result(result, results)
            elif result['type'] == 'variable triggered result':
                elements += cls.add_variable_triggered_result(result, results)
            elif result['type'] == 'accumulated results':
                elements += cls.add_accumulated_results()
        elements += cls.add_results(data, results)
        elements += cls.add_links(data, results)
        for result in data['results']:
            if result['type'] == 'text':
                elements += cls.add_text(result)
        return elements

    @classmethod
    def calculate_results(cls, data, results_data):
        """ Calculate the result values based on question answer data """
        calculatedResults = ResultData()
        for index in range(1, len(results_data)-2):
            results = results_data[str(index)]
            for result in results:
                cls.process_result(data, index, result, calculatedResults)
                
        return calculatedResults

    @classmethod
    def process_result(cls, data, index, result, calculatedResults):
        for answer in data['questions'][index-1]['answers']:
            if answer['body'] == result:
                cls.process_actions(answer, calculatedResults)
                break

    @classmethod
    def process_actions(cls, answer, calculatedResults):
        for action in answer['actions']:
            if action['type'] == 'points':
                cls.set_points(calculatedResults, action)
            elif action['type'] == 'link':
                calculatedResults.links.append(action['value'])
            elif action['type'] == 'result':
                calculatedResults.result_items.append(action['value'])
            elif action['type'] =='set variable':
                cls.set_variable(calculatedResults, action)

    @staticmethod
    def set_points(calculatedResults, action):
        if action['operator'] == '+':
            calculatedResults.points += int(action.get('value',0))
        elif action['operator'] == '-':
            calculatedResults.points -= int(action.get('value',0))

    @staticmethod
    def set_variable(calculatedResults, action):
        sub_type_value = calculatedResults.variables.get(action['sub_type'], 0)
        if action['operator'] == '+':
            calculatedResults.variables[action['sub_type']] = sub_type_value + int(action['value'])
        elif action['operator'] == '-':
            calculatedResults.variables[action['sub_type']] = sub_type_value - int(action['value'])

    @staticmethod
    def add_progress_bar(result, results, index):
        """ Add progress bar elements """
        bar_value = 0
        if result['p3'] == 'Points':
            bar_value = results.points
        else:
            bar_value = results.variables.get(result['p3'], 0)
        elements = '<div style="width:100%">'
        elements += '<h2>{} {}</h2>'.format(result['text'], bar_value)
        elements += '<progress id="progress_{}" value="{}" min="{}" max="{}" style="width:100%;height:3em"></progress><br/>'.format(index, bar_value, result['p1'], result['p2'])
        elements += '<table style="margin:0">'
        elements += '<tr>'
        elements += '<td style="border:0;padding:0">{}</td><td style="text-align:right;border:0;padding:0">{}</td>'.format(result['p1'], result['p2'])
        elements += '<tr>'
        elements += '</table>'
        elements += '</br>'
        elements += '</div>'
        return elements

    @staticmethod
    def add_points_triggered_result(result, results):
        """ Add points triggered results elements """
        elements = ''
        if results.points >= int(result['p1']) and results.points <= int(result['p2']):
            elements += '{}</br>'.format(result['text'])
        return elements
           
    @staticmethod
    def add_variable_triggered_result(result, results):
        """ Add variable triggered results elements """
        elements = ''
        variable_name = result['p3']
        variable_value = results.variables.get(variable_name, -1)
        if variable_value == -1:
            return elements
        if variable_value >= int(result['p1']) and variable_value <= int(result['p2']):
            elements += '<p>{}</p>'.format(result['text'])
        return elements
          
    @staticmethod
    def add_accumulated_results():
        """ Add accumulated results elements """
        elements = ''
        return elements
        
    @staticmethod
    def add_text(result):
        """ Add text results elements """
        elements = '{}</br></br>'.format(result['text'])
        return elements

    @staticmethod
    def add_results(data, results):
        """ Add results items elements """
        elements = '<ul>'
        for result in results.result_items:
            text = ''
            for result_item in data['result_items']:
                if result_item['id'] == result:
                    text = result_item['text']
                    break
            elements += '<li>{}</li>'.format(text)
        elements += '</ul>'
        return elements

    @staticmethod
    def add_links(data, results):
        """ Add links elements """
        elements = ''
        for link in results.links:
            text = ''
            for link_item in data['link_items']:
                if link_item['id'] == link:
                    text = link_item['text']
                    link_url = link_item['link_url']
                    break
            elements = '<a href="{}">{}</a>'.format(link_url, text)
            if elements:
                elements += '</br></br>'
        return elements

    @staticmethod
    def create_info_box(data, info_box_id):
        """ Add info box elements """
        elements = ''
        for info_box in data.get('info_boxes'):
            if info_box['id'] == info_box_id:
                elements += '<details class="nhsuk-details">'
                elements += '<summary class="nhsuk-details__summary" role="button">'
                elements += '<span class="nhsuk-details__summary-text">{}</span>'.format(info_box['title'])
                elements += '</summary>'
                elements += '<div class="nhsuk-details__text">{}</div></details>'.format(info_box['body'])
        return elements



class ResultData(object):
    """ Class to hold the results of a single questionnaire """
    def __init__(self):
        self._points = 0
        self._variables = {}
        self._links = []
        self._result_items = []

    @property
    def points(self):
        return self._points

    @points.setter
    def points(self, value):
        self._points = value

    @property
    def variables(self):
        return self._variables

    @property
    def links(self):
        return self._links

    @property
    def result_items(self):
        return self._result_items
