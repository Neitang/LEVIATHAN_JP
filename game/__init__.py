from otree.api import *

from .models import Constants as C, Subsession, Group, Player  # type: ignore
from .pages import (
    PowerTransfer,
    PowerTransferWait,
    PowerTransferResult,
    Contribution,
    ContributionWaitPage,
    ContributionResult,
    Punishment,
    PunishmentWaitPage,
    RoundResult,
    FinalResult,
)  # type: ignore

doc = """
Public goods game with punishment for the Leviathan project.
"""

page_sequence = [
    PowerTransfer,
    PowerTransferWait,
    PowerTransferResult,
    Contribution,
    ContributionWaitPage,
    ContributionResult,
    Punishment,
    PunishmentWaitPage,
    RoundResult,
    FinalResult,
]
