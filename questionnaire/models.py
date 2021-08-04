from django.db import models
from wagtail.core.models import Page
from wagtail.admin.edit_handlers import FieldPanel
import requests


class Questionnaire(Page):
    json_url = models.CharField(max_length=250)

    content_panels = Page.content_panels + [
        FieldPanel('json_url', classname="full")
    ]

    def get_context(self, request):
        context = super().get_context(request)
        step_number = int(request.GET.get('p', 0))
        session_key_data = 'form_data-%s' % self.pk

        session_data = request.session.get(session_key_data, {})
        if session_data.get('data'):
            data = session_data['data']
        else:
            data = requests.get(self.json_url).json()
            session_data['data'] = data
            request.session[session_key_data] = session_data

        if request.method == 'POST' and step_number > 0:
            posted_answer = request.POST.getlist('answer')
            session_data[step_number - 1] = posted_answer
            request.session[session_key_data] = session_data
            

        questionnaire_elements = ''

        if step_number == 0:
            questionnaire_elements = self.create_intro(data)
        elif step_number > len(data['questions']):
            results_data = request.session.get(session_key_data, {})
            questionnaire_elements = self.create_result(data, results_data)
        else:
            questionnaire_elements = self.create_question(data, step_number - 1)


        context['question_number'] = step_number
        context['total_questions'] = len(data['questions'])
        context['questionnaire_elements'] = questionnaire_elements
        context['next_step'] = step_number + 1
        context['prev_step'] = step_number - 1

        return context

    def create_intro(self, data):
        elements = ''
        elements += '<h1>{}</h1>'.format(data['config']['title'])
        elements += '<h2>{}</h2>'.format(data['config']['intro_title'])
        elements += data['config']['intro_copy']
        return elements

    def create_question(self, data, question_number):
        elements = ''
        question = data['questions'][question_number]
        elements += '<b>{}</b></br>'.format(question['body'])
        if question['info_box']:
            elements += self.create_info_box(data, question['info_box'])
        if question['type'] == 'single select':
            elements += self.create_single_select(question)
        elif question['type'] == 'multiple select':
            elements += self.create_multi_select(question)
        return elements

    def create_single_select(self, question):
        elements = '<ul>'
        answer_index = 0
        for answer in question['answers']:
            elements += '<li>'
            elements += '<input type="radio" name="answer" value="{}" required id="radio_{}">'.format(answer['body'], answer_index)
            elements += '<label for="radio_{}">{}</label>'.format(answer_index, answer['body'])
            elements += '</li>'
            answer_index += 1
        elements += '</ul>'
        return elements

    def create_multi_select(self, question):
        elements = '<ul>'
        answer_index = 0
        for answer in question['answers']:
            elements += '<li>'
            elements += '<input type="checkbox" name="answer" value="{}" id="checkbox_{}">'.format(answer['body'], answer_index)
            elements += '<label for="checkbox_{}">{}</label>'.format(answer_index, answer['body'])
            elements += '</li>'
            answer_index += 1
        elements += '</ul>'
        return elements

    def create_result(self, data, results_data):
        results = self.calculate_results(data, results_data)
        elements = ''
        index = 0
        for result in data['results']:
            if result['type'] == 'progress bar':
                elements += self.add_progress_bar(result, results, index)
            elif result['type'] == 'points triggered result':
                elements += self.add_points_triggered_result(result, results, index)
            elif result['type'] == 'variable triggered result':
                elements += self.add_variable_triggered_result(result, results, index)
            elif result['type'] == 'accumulated results':
                elements += self.add_accumulated_results(result, results, index)
        elements += self.add_results(data, results)
        elements += self.add_links(data, results)
        for result in data['results']:
            if result['type'] == 'text':
                elements += self.add_text(result, results, index)
        return elements

    def calculate_results(self, data, results_data):
        calculatedResults = ResultData()
        for index in range(1, len(results_data)-2):
            results = results_data[str(index)]
            for result in results:
                answers = data['questions'][index-1]['answers']
                for answer in answers:
                    if answer['body'] == result:
                        for action in answer['actions']:
                            if action['type'] == 'points':
                                if action['operator'] == '+':
                                    calculatedResults.points += int(action.get('value',0))
                                elif action['operator'] == '-':
                                    calculatedResults.points -= int(action.get('value',0))
                            elif action['type'] == 'link':
                                calculatedResults.links.append(action['value'])
                            elif action['type'] == 'result':
                                calculatedResults.result_items.append(action['value'])
                            elif action['type'] =='set variable':
                                sub_type_value = calculatedResults.variables.get(action['sub_type'], 0)
                                if action['operator'] == '+':
                                    calculatedResults.variables[action['sub_type']] = sub_type_value + int(action['value'])
                                elif action['operator'] == '-':
                                    calculatedResults.variables[action['sub_type']] = sub_type_value - int(action['value'])
                        break
        return calculatedResults



    
    def add_progress_bar(self, result, results, index):
        bar_value = 0
        if result['p3'] == 'Points':
            bar_value = results.points
        else:
            bar_value = results.variables[result['p3']]
        elements = '<h2>{} {}</h2>'.format(result['text'], bar_value)
        elements += '<progress id="progress_{}" value="{}" min="{}" max="{}"></progress><br/>'.format(index, bar_value, result['p1'], result['p2'])
        return elements

    def add_points_triggered_result(self, result, results, index):
        elements = ''
        if results.points >= int(result['p1']) and results.points <= int(result['p2']):
            elements += '{}</br>'.format(result['text'])
        return elements
           
    def add_variable_triggered_result(self, result, results, index):
        elements = ''
        variable_name = result['p3']
        variable_value = results.variables.get(variable_name, -1)
        if variable_value == -1:
            return elements
        if variable_value >= int(result['p1']) and variable_value <= int(result['p2']):
            elements += '{}</br></br>'.format(result['text'])
        return elements
          
    def add_accumulated_results(self, result, results, index):
        elements = ''
        return elements
        
    def add_text(self, result, results, index):
        elements = ''
        elements += '{}</br></br>'.format(result['text'])
        return elements

    def add_results(self, data, results):
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

    def add_links(self, data, results):
        elements = ''
        for link in results.links:
            text = ''
            for link_item in data['link_items']:
                if link_item['id'] == link:
                    text = link_item['text']
                    link_url = link_item['link_url']
                    break
            elements += '<a href="{}">{}</a>'.format(link_url, text)
            if elements:
                elements += '</br></br>'
        return elements

    # elements += self.create_info_box(data, question['info_box'])
    def create_info_box(self, data, info_box_id):
        elements = ''
        for info_box in data.get('info_boxes'):
            if info_box['id'] == info_box_id:
                elements += '<details style="display:inline;"><summary>{}</summary>{}</details>'.format(info_box['title'], info_box['body'])
        return elements



class ResultData(object):

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