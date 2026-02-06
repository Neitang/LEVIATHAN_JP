from otree.api import *

from .pages import Questionnaire  # type: ignore


doc = """
Survey module for Leviathan project
"""


class C(BaseConstants):
    NAME_IN_URL = 'survey'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    pass


page_sequence = [Questionnaire]
