from otree.api import (
    models,
    widgets,
    BaseConstants,
    BaseSubsession,
    BaseGroup,
    BasePlayer,
    Currency as c,
    currency_range,
)

doc = """
Public Goods Game with Punishment (Fixed)
"""

class Constants(BaseConstants):
    name_in_url = 'game'
    players_per_group = 5
    num_rounds = 20
    
    # settings.py からパラメータを取得
    # settings.py で未定義の場合は以下のデフォルトを使用
    endowment = 20
    multiplier = 1.5
    deduction_points = 10
    punishment_cost = 1
    power_effectiveness = 1

class Subsession(BaseSubsession):
    def creating_session(self):
        # session.config から実験設定を読み込み、settings.py で柔軟に変更可能にする
        self.group_randomly()
        players = self.get_players()

        for p in players:
            if self.round_number == 1:
                initial_power = 1.0
                p.participant.vars['cumulative_payoff'] = c(0)
                p.participant.vars['punishment_power'] = initial_power
            else:
                prev_round = p.in_round(self.round_number - 1)
                initial_power = prev_round.punishment_power_after or p.participant.vars.get('punishment_power', 1.0)
                p.participant.vars['punishment_power'] = initial_power

            p.punishment_power_before = initial_power
            p.punishment_power_after = initial_power
            p.power_transfer_out_total = 0
            p.power_transfer_in_total = 0
            p.power_transfer_cost = c(0)
            p.available_endowment = c(self.session.config.get('endowment', Constants.endowment))
            p.can_receive_punishment = True
            p.available_before_contribution = p.available_endowment
            p.available_before_punishment = p.available_endowment
            p.attempted_punishment_cost = c(0)
            p.attempted_punishment_points = 0
            p.punishment_points_given_actual = 0
            p.punishment_points_received_actual = 0

            for i in range(1, Constants.players_per_group + 1):
                setattr(p, f'power_transfer_p{i}', 0)


class Group(BaseGroup):
    total_contribution = models.CurrencyField()
    individual_share = models.CurrencyField()

    def set_group_contribution(self):
        """グループの総貢献額と各自の取り分を計算"""
        players = self.get_players()
        contributions = [p.contribution or 0 for p in players]
        self.total_contribution = sum(contributions)
        group_size = len(players) or 1
        multiplier = self.session.config.get('contribution_multiplier', Constants.multiplier)
        share_value = float(self.total_contribution) * float(multiplier) / group_size
        self.individual_share = c(share_value)

    def set_payoff(self):
        """懲罰フェーズ終了後に各プレイヤーの利得を確定"""
        self.adjust_punishments()
        for player in self.get_players():
            player.set_payoff()

    def adjust_punishments(self):
        session = self.session
        players = self.get_players()
        cost_per_point = session.config.get('punishment_cost', 1)
        effectiveness_base = session.config.get('power_effectiveness', Constants.power_effectiveness)

        actual_cost = {p: 0.0 for p in players}
        actual_points_sent = {p: 0.0 for p in players}

        for victim in players:
            victim_available = float(victim.available_before_punishment or victim.available_endowment or 0)
            punish_entries = []
            total_loss = 0.0
            for punisher in players:
                if punisher.id_in_group == victim.id_in_group:
                    continue
                attempted_points = getattr(punisher, f'punish_p{victim.id_in_group}', 0) or 0
                if attempted_points <= 0:
                    continue
                effective_power = punisher.punishment_power_after or punisher.participant.vars.get('punishment_power', 1.0)
                loss_per_point = effectiveness_base * effective_power
                total_loss += attempted_points * loss_per_point
                punish_entries.append((punisher, attempted_points, loss_per_point))

            if total_loss <= victim_available + 1e-9:
                scale = 1.0
            else:
                if total_loss <= 0 or victim_available <= 0:
                    scale = 0.0
                else:
                    scale = victim_available / total_loss

            actual_loss = 0.0
            received_points = 0.0
            for punisher, attempted_points, loss_per_point in punish_entries:
                points_used = round(attempted_points * scale, 6)
                loss = points_used * loss_per_point
                actual_loss += loss
                received_points += points_used

                actual_points_sent[punisher] += points_used
                actual_cost[punisher] += points_used * cost_per_point

            victim_available = max(0.0, victim_available - actual_loss)
            victim.available_endowment = c(victim_available)
            victim.punishment_points_received_actual = received_points
            victim.punishment_received = c(actual_loss)
            if victim_available <= 0:
                victim.can_receive_punishment = False

        for punisher in players:
            attempted_cost = float(punisher.attempted_punishment_cost or 0)
            actual_cost_value = min(actual_cost[punisher], attempted_cost)

            available_before = float(punisher.available_before_punishment or punisher.available_endowment or 0)
            new_available = max(0.0, available_before - actual_cost_value)
            punisher.available_endowment = c(new_available)
            punisher.punishment_given = c(actual_cost_value)
            punisher.punishment_points_given_actual = actual_points_sent[punisher]
            if new_available <= 0:
                punisher.can_receive_punishment = False


class Player(BasePlayer):
    contribution = models.CurrencyField(
        min=0,
        max=Constants.endowment,
        initial=0,
    )

    def contribution_max(self):
        if self.available_endowment is not None:
            return self.available_endowment
        return self.session.config['endowment']

    # 各プレイヤーに与える罰ポイントを入力するフィールド
    # グループは最大5人を想定し、id_in_group は 1〜5
    punish_p1 = models.IntegerField(min=0, initial=0, label="プレイヤー1への罰ポイント")
    punish_p2 = models.IntegerField(min=0, initial=0, label="プレイヤー2への罰ポイント")
    punish_p3 = models.IntegerField(min=0, initial=0, label="プレイヤー3への罰ポイント")
    punish_p4 = models.IntegerField(min=0, initial=0, label="プレイヤー4への罰ポイント")
    punish_p5 = models.IntegerField(min=0, initial=0, label="プレイヤー5への罰ポイント")

    punishment_given = models.CurrencyField(doc="与えた罰の総コスト")
    punishment_received = models.CurrencyField(doc="受けた罰による総損失")

    # 罰威力の移譲に関するフィールド
    power_transfer_p1 = models.FloatField(min=0, initial=0, blank=True)
    power_transfer_p2 = models.FloatField(min=0, initial=0, blank=True)
    power_transfer_p3 = models.FloatField(min=0, initial=0, blank=True)
    power_transfer_p4 = models.FloatField(min=0, initial=0, blank=True)
    power_transfer_p5 = models.FloatField(min=0, initial=0, blank=True)

    power_transfer_out_total = models.FloatField(initial=0, blank=True)
    power_transfer_in_total = models.FloatField(initial=0, blank=True)
    punishment_power_before = models.FloatField(initial=1.0, blank=True)
    punishment_power_after = models.FloatField(initial=1.0, blank=True)
    power_transfer_cost = models.CurrencyField(initial=c(0), blank=True)
    available_endowment = models.CurrencyField(initial=Constants.endowment, blank=True)
    can_receive_punishment = models.BooleanField(initial=True)
    available_before_contribution = models.CurrencyField(initial=Constants.endowment, blank=True)
    available_before_punishment = models.CurrencyField(initial=Constants.endowment, blank=True)
    attempted_punishment_cost = models.CurrencyField(initial=c(0), blank=True)
    attempted_punishment_points = models.FloatField(initial=0, blank=True)
    punishment_points_given_actual = models.FloatField(initial=0, blank=True)
    punishment_points_received_actual = models.FloatField(initial=0, blank=True)

    # payoff フィールドは oTree が自動生成するため、後で値を代入する

    def set_payoff(self):
        """今ラウンドの最終利得を計算"""
        # 懲罰に関する計算
        # 1. 自分が与えた罰点とコストを集計
        punishment_points_given = self.punishment_points_given_actual
        if punishment_points_given in (None, 0):
            punishment_points_given = 0
            punishment_fields = [self.punish_p1, self.punish_p2, self.punish_p3, self.punish_p4, self.punish_p5]
            for i in range(len(punishment_fields)):
                if (i + 1) != self.id_in_group:
                    punishment_points_given += punishment_fields[i] if punishment_fields[i] is not None else 0
            self.punishment_points_given_actual = punishment_points_given
            self.punishment_given = c(punishment_points_given * self.session.config['punishment_cost'])

        # 2. 自分が受けた罰点と損失を集計
        punishment_points_received = self.punishment_points_received_actual
        if punishment_points_received in (None, 0):
            punishment_points_received = 0
            punishment_loss = 0
            effectiveness_base = self.session.config.get('power_effectiveness', Constants.power_effectiveness)
            if self.can_receive_punishment:
                for other_player in self.get_others_in_group():
                    field_name = f'punish_p{self.id_in_group}'
                    points = getattr(other_player, field_name, 0) or 0
                    punishment_points_received += points
                    effective_power = other_player.punishment_power_after or other_player.participant.vars.get('punishment_power', 1.0)
                    punishment_loss += points * effectiveness_base * effective_power
            self.punishment_points_received_actual = punishment_points_received
            self.punishment_received = c(punishment_loss)

        # 3. 式に基づいて最終利得を算出
        # π_i = E - c_i + (m/n)Σc_j - pc*Σd_ij - pe*Σd_ji
        payoff_before_punishment = (
            self.session.config['endowment'] - self.contribution + self.group.individual_share
        )
        total_costs = self.punishment_given + self.punishment_received + self.power_transfer_cost
        self.payoff = payoff_before_punishment - total_costs
        
        # 累積利得を更新
        if 'cumulative_payoff' not in self.participant.vars:
            self.participant.vars['cumulative_payoff'] = c(0)
        self.participant.vars['cumulative_payoff'] += self.payoff
        self.participant.vars['punishment_power'] = self.punishment_power_after
