# introduction/pages.py

from otree.api import Page, WaitPage

from .models import Constants

class Introduction(Page): # 以前のバージョンでは IntroductionFixed だったページ
    @staticmethod
    def vars_for_template(player):
        return {
            'treatment_name': player.session.config['treatment_name']
        }

class Test(Page): # 以前のバージョンでは TestFixed だったページ
    form_model = 'player'

    @staticmethod
    def get_form_fields(player):
        treatment = player.session.config['treatment_name']
        if treatment == 'fixed':
            return ['q1_fixed', 'q2_fixed']
        elif treatment == 'transfer_free':
            return ['q2_transfer_free', 'q3_transfer_free']
        elif treatment == 'transfer_cost':
            return ['q2_transfer_cost', 'q1_transfer_cost']
        return []

    @staticmethod
    def vars_for_template(player):
        return {
            'treatment_name': player.session.config['treatment_name']
        }

    @staticmethod
    def error_message(player, values):
        treatment = player.session.config['treatment_name']
        # 注意: ここで求める正解は実験設計に合わせて設定してください
        if treatment == 'fixed':
            if values['q1_fixed'] != player.session.config['endowment'] or \
               values['q2_fixed'] != player.session.config['contribution_multiplier']:
                return (
                    f"固定条件の解答が正しくありません。初期保有額は{player.session.config['endowment']}、"
                    f"公共財の乗数は{player.session.config['contribution_multiplier']}です。もう一度確認してください。"
                )
        elif treatment == 'transfer_free':
            # 罰威力は移譲可能で、移譲コストは設定値。最大移譲ポイントは初期の罰ポイント
            expected_cost = player.session.config.get('power_transfer_cost_rate', 0)
            provided_cost = values.get('q2_transfer_free')
            cost_correct = (
                provided_cost is not None
                and abs(provided_cost - expected_cost) <= 1e-6
            )
            if not cost_correct or \
               values['q3_transfer_free'] != player.session.config['deduction_points']:
                return (
                    "無コスト移譲条件の解答が正しくありません。罰威力は移譲可能で、移譲コストは"
                    f"{expected_cost:.1f}、"
                    f"最大移譲ポイントは{player.session.config['deduction_points']}です。もう一度確認してください。"
                )
        elif treatment == 'transfer_cost':
            # 罰威力は移譲可能でコスト率が設定値、移譲時にコストが発生すると仮定
            expected_rate = player.session.config['power_transfer_cost_rate']
            cost_required_answer = values.get('q2_transfer_cost')
            provided_rate = values.get('q1_transfer_cost')
            rate_correct = (
                provided_rate is not None
                and abs(provided_rate - expected_rate) <= 1e-6
            )
            if cost_required_answer != 'yes' or not rate_correct:
                return (
                    "コストあり移譲条件の解答が正しくありません。移譲コスト率は"
                    f"{expected_rate:.1f}であり、罰威力を移譲する際にはコストが必要です。"
                    "もう一度確認してください。"
                )

page_sequence = [Introduction, Test]
