# survey/pages.py

from otree.api import *

class Questionnaire(Page):
    def vars_for_template(self):
        return {
            'treatment_name': self.session.config['treatment_name']
        }

page_sequence = [Questionnaire]