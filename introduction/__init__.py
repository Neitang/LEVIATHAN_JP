from otree.api import *

from .models import Constants as C, Subsession, Group, Player  # type: ignore
from .pages import Introduction, Test  # type: ignore


doc = """
Introduction app for Leviathan project
"""


page_sequence = [Introduction, Test]
