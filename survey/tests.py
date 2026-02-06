from otree.api import Bot

from . import pages


class PlayerBot(Bot):
    def play_round(self):
        yield pages.Questionnaire
