from otree.api import Bot, Submission

from . import pages
from .models import Constants


def punishment_form(player, points):
    data = {}
    for i in range(1, Constants.players_per_group + 1):
        if i == player.id_in_group:
            continue
        data[f'punish_p{i}'] = points
    return data


def power_transfer_form(player, amount):
    data = {}
    for i in range(1, Constants.players_per_group + 1):
        if i == player.id_in_group:
            continue
        data[f'power_transfer_p{i}'] = amount
    return data


class PlayerBot(Bot):
    def play_round(self):
        treatment = self.session.config.get('treatment_name', 'fixed')

        if treatment in {'transfer_free', 'transfer_cost'}:
            # Power transfer from round 3 onwards
            if self.player.round_number >= 3:
                yield Submission(
                    pages.PowerTransfer,
                    power_transfer_form(self.player, 0.1),
                    check_html=False,
                )
                yield pages.PowerTransferResult

            # Contribution: 10 MUs each round
            yield Submission(pages.Contribution, {'contribution': 10}, check_html=False)
            yield pages.ContributionResult

            if self.player.round_number > 1:
                # Punish every other participant with 1 point (cost 1 MU per point)
                yield Submission(
                    pages.Punishment,
                    punishment_form(self.player, 1),
                    check_html=False,
                )
                yield pages.RoundResult

            if self.player.round_number == Constants.num_rounds:
                yield pages.FinalResult

        else:  # fixed treatment default bot
            yield Submission(pages.Contribution, {'contribution': 0}, check_html=False)
            yield pages.ContributionResult

            if self.player.round_number > 1:
                yield Submission(
                    pages.Punishment,
                    punishment_form(self.player, 0),
                    check_html=False,
                )
                yield pages.RoundResult

            if self.player.round_number == Constants.num_rounds:
                yield pages.FinalResult
