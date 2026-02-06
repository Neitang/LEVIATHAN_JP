from otree.api import Bot, Submission

from . import pages


class PlayerBot(Bot):
    def play_round(self):
        treatment = self.session.config.get('treatment_name')
        yield pages.Introduction

        endowment = self.session.config['endowment']
        multiplier = self.session.config['contribution_multiplier']
        deduction_points = self.session.config['deduction_points']
        transfer_cost_rate = self.session.config.get('power_transfer_cost_rate', 0)

        if treatment == 'fixed':
            form_data = dict(q1_fixed=endowment, q2_fixed=multiplier)
        elif treatment == 'transfer_free':
            form_data = dict(
                q2_transfer_free=0,
                q3_transfer_free=deduction_points,
            )
        elif treatment == 'transfer_cost':
            form_data = dict(
                q2_transfer_cost='yes',
                q1_transfer_cost=transfer_cost_rate,
            )
        else:
            form_data = {}

        yield Submission(pages.Test, form_data, check_html=False)
