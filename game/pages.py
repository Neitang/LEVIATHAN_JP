# game/pages.py

from otree.api import Page, WaitPage

from .models import Constants
from otree.api import Currency as c # Currency をインポートするための別名


def build_history_rounds(player):
    """Collect per-round history data for templates."""
    session = player.session
    endowment = session.config.get('endowment', 0)
    endowment_currency = c(endowment)
    rounds = []

    for prev in player.in_previous_rounds():
        group = prev.group
        members = group.get_players()

        player_entries = []
        has_power_transfer = (
            session.config.get('power_transfer_allowed')
            and prev.round_number >= 3
        )

        for member in members:
            total_sent = 0
            for other in members:
                if other.id_in_group == member.id_in_group:
                    continue
                field_name = f'punish_p{other.id_in_group}'
                total_sent += getattr(member, field_name, 0) or 0

            effective_sent_points = getattr(member, 'punishment_points_given_actual', None)
            if effective_sent_points is None:
                effective_sent_points = total_sent

            player_entries.append(
                dict(
                    id_in_group=member.id_in_group,
                    contribution=member.contribution,
                    endowment=endowment_currency,
                    available_endowment=member.available_endowment,
                    punishment_sent_total=effective_sent_points,
                    punishment_received_total=member.punishment_received,
                    power_before=member.punishment_power_before,
                    power_after=member.punishment_power_after,
                    power_after_display=f"{member.punishment_power_after:.1f}",
                    power_transfer_out=member.power_transfer_out_total,
                    power_transfer_out_display=f"{member.power_transfer_out_total:.1f}",
                    power_transfer_in=member.power_transfer_in_total,
                    power_transfer_in_display=f"{member.power_transfer_in_total:.1f}",
                    power_transfer_cost=member.power_transfer_cost,
                )
            )

        effectiveness_base = session.config.get('power_effectiveness', Constants.power_effectiveness)
        matrix_rows = []
        for victim in members:
            actual_loss = float(victim.punishment_received or 0)
            if actual_loss <= 0:
                victim_before = float(victim.available_before_punishment or victim.available_endowment or 0)
                victim_after = float(victim.available_endowment or 0)
                diff = victim_before - victim_after
                if diff > actual_loss:
                    actual_loss = max(0.0, diff)

            attempted_loss = 0.0
            attempted_points = {}
            effective_power_map = {}
            for giver in members:
                if giver.id_in_group == victim.id_in_group:
                    continue
                points = getattr(giver, f'punish_p{victim.id_in_group}', 0) or 0
                attempted_points[giver.id_in_group] = points
                effective_power = (
                    giver.punishment_power_after
                    or giver.participant.vars.get('punishment_power', 1.0)
                )
                effective_power_map[giver.id_in_group] = effective_power
                if points > 0:
                    attempted_loss += points * effectiveness_base * effective_power

            if attempted_loss <= 0:
                scale = 0.0
            else:
                scale = min(1.0, actual_loss / attempted_loss)

            cells = []
            total_received = 0.0
            for giver in members:
                is_self = giver.id_in_group == victim.id_in_group
                if is_self:
                    cells.append(dict(is_self=True, amount=None, amount_display=None))
                else:
                    points_attempted = attempted_points.get(giver.id_in_group, 0)
                    points_used = round(points_attempted * scale, 6)
                    effective_power = effective_power_map.get(
                        giver.id_in_group,
                        giver.punishment_power_after
                        or giver.participant.vars.get('punishment_power', 1.0),
                    )
                    actual_loss_value = points_used * effectiveness_base * effective_power
                    total_received += actual_loss_value
                    loss_display = c(actual_loss_value)
                    cells.append(
                        dict(
                            is_self=False,
                            amount=loss_display,
                            amount_display=loss_display,
                        )
                    )

            if victim.punishment_received is not None:
                summary_loss = victim.punishment_received
            else:
                summary_loss = c(total_received)

            for entry in player_entries:
                if entry['id_in_group'] == victim.id_in_group:
                    entry['punishment_received_total'] = summary_loss
                    break

            matrix_rows.append(dict(victim_id=victim.id_in_group, cells=cells))

        transfer_rows = []
        if has_power_transfer:
            for giver in members:
                cells = []
                for receiver in members:
                    is_self = giver.id_in_group == receiver.id_in_group
                    amount = None
                    if not is_self:
                        field_name = f'power_transfer_p{receiver.id_in_group}'
                        amount = getattr(giver, field_name, 0) or 0
                    cells.append(
                        dict(
                            is_self=is_self,
                            amount=amount,
                            amount_display=(f"{amount:.1f}" if amount is not None else None),
                        )
                    )
                transfer_rows.append(dict(giver_id=giver.id_in_group, cells=cells))

        rounds.append(
            dict(
                round_number=prev.round_number,
                players=player_entries,
                matrix_rows=matrix_rows,
                transfer_rows=transfer_rows,
                has_punishment=prev.round_number > 1,
                has_power_transfer=has_power_transfer,
            )
        )

    return rounds

# =============================================================================
# CLASS: Contribution
# =============================================================================
class Contribution(Page):
    form_model = 'player'
    form_fields = ['contribution']

    @staticmethod
    def vars_for_template(player):
        # _HistoryModal.html の player.in_all_rounds イテレータが正しい id_range を得られるようにする
        id_range = list(range(1, Constants.players_per_group + 1))
        return dict(
            history=player.in_previous_rounds(),
            id_range=id_range,
            C=Constants,
            history_rounds=build_history_rounds(player),
            available_endowment=player.available_endowment,
        )

    @staticmethod
    def error_message(player, values):
        contribution = values.get('contribution')
        if contribution is None:
            return '貢献額を入力してください。'
        endowment = player.session.config.get('endowment', Constants.endowment)
        amount = float(contribution)
        available = float(player.available_endowment or endowment)
        if amount < 0 or amount > available:
            limit = int(available)
            return f'貢献額は0から{limit}までの範囲で入力してください。'
        if not amount.is_integer():
            return '貢献額は整数で入力してください。'
        return None

    @staticmethod
    def before_next_page(player, timeout_happened):
        endowment = player.session.config.get('endowment', Constants.endowment)
        available = player.available_endowment if player.available_endowment is not None else c(endowment)
        player.available_before_contribution = available
        remaining = available - player.contribution
        if remaining < c(0):
            remaining = c(0)
        player.available_endowment = remaining
        player.available_before_punishment = remaining
        if remaining <= c(0):
            player.can_receive_punishment = False
        player.participant.vars['contribution_submitted_round'] = player.round_number

# =============================================================================
# CLASS: ContributionWaitPage
# =============================================================================
class ContributionWaitPage(WaitPage):
    template_name = "game/ContributionWait.html"

    @staticmethod
    def after_all_players_arrive(group):
        group.set_group_contribution()
        if group.round_number == 1:
            for player in group.get_players():
                player.set_payoff()

    @staticmethod
    def vars_for_template(player):
        players = player.group.get_players()
        current_round = player.round_number
        submitted = sum(
            1
            for p in players
            if p.participant.vars.get('contribution_submitted_round') == current_round
        )
        total = len(players)
        return dict(waiting_progress=submitted, waiting_total=total)

# =============================================================================
# CLASS: ContributionResult
# =============================================================================
class ContributionResult(Page):
    @staticmethod
    def vars_for_template(player):
        session = player.session
        endowment = session.config['endowment']
        endowment_currency = c(endowment)
        share = player.group.individual_share

        players_data = []
        for member in player.group.get_players():
            contribution = member.contribution
            received_from_public = share
            remaining = member.available_endowment or c(0)
            available_before = member.available_before_contribution or remaining + contribution
            kept_amount = remaining
            current_total = kept_amount + share

            players_data.append(
                dict(
                    player=member,
                    contribution=contribution,
                    received_from_public=received_from_public,
                    current_total=current_total,
                    available_endowment=remaining,
                    available_before_contribution=available_before,
                )
            )

        return dict(
            players_data=players_data,
            endowment=endowment_currency,
            share=share,
        )


class PowerTransfer(Page):
    form_model = "player"

    @staticmethod
    def is_displayed(player):
        session = player.session
        return session.config.get("power_transfer_allowed") and player.round_number >= 3

    @staticmethod
    def get_form_fields(player):
        return [
            f"power_transfer_p{i}"
            for i in range(1, Constants.players_per_group + 1)
            if i != player.id_in_group
        ]

    @staticmethod
    def vars_for_template(player):
        session = player.session
        transfer_unit = session.config.get("punishment_transfer_unit", 0.1)
        cost_per_unit = session.config.get("power_transfer_cost_rate", 0)
        others_data = []
        for other in player.get_others_in_group():
            others_data.append(
                dict(
                    id_in_group=other.id_in_group,
                    player_code=f"player {other.id_in_group}",
                    contribution=other.contribution,
                    current_power=other.punishment_power_before,
                )
            )

        is_costly = session.config.get("costly_punishment_transfer", False)

        return dict(
            current_power=player.punishment_power_before,
            current_power_display=f"{player.punishment_power_before:.1f}",
            transfer_unit=transfer_unit,
            transfer_unit_display=f"{transfer_unit:.1f}",
            others_data=others_data,
            max_transfer=player.punishment_power_before,
            is_costly=is_costly,
            transfer_cost_rate=cost_per_unit,
            transfer_cost_per_unit=cost_per_unit,
            cost_per_unit=cost_per_unit,
            cost_per_unit_display=f"{cost_per_unit:.1f}",
            currency_label=session.config.get('real_world_currency_code', 'MU'),
            players_status=[],
        )

    @staticmethod
    def error_message(player, values):
        transfer_unit = player.session.config.get("punishment_transfer_unit", 0.1)
        tolerance = 1e-6
        total = 0
        for value in values.values():
            if value is None:
                continue
            if value < -tolerance:
                return "譲渡量は0以上で入力してください。"
            total += value
            if transfer_unit > 0:
                multiples = value / transfer_unit
                if abs(multiples - round(multiples)) > 1e-6:
                    return f"譲渡量は {transfer_unit} の倍数で入力してください。"

        if total - player.punishment_power_before > tolerance:
            return "譲渡量の合計が保有する罰威力を超えています。"

    @staticmethod
    def before_next_page(player, timeout_happened):
        session = player.session
        transfer_fields = [
            f"power_transfer_p{i}"
            for i in range(1, Constants.players_per_group + 1)
            if i != player.id_in_group
        ]
        total_out = 0
        for field in transfer_fields:
            total_out += getattr(player, field, 0) or 0
        player.power_transfer_out_total = round(total_out, 3)

        unit = session.config.get("punishment_transfer_unit", 0.1)
        rate = session.config.get("power_transfer_cost_rate", 0)
        if session.config.get("costly_punishment_transfer") and unit > 0:
            units = total_out / unit
            cost_value = units * rate
            player.power_transfer_cost = c(cost_value)
        else:
            player.power_transfer_cost = c(0)

        player.punishment_power_after = max(
            0,
            player.punishment_power_before - player.power_transfer_out_total,
        )
        player.participant.vars['power_transfer_submitted_round'] = player.round_number


class PowerTransferWait(WaitPage):
    template_name = "game/PowerTransferWait.html"

    @staticmethod
    def is_displayed(player):
        session = player.session
        return session.config.get("power_transfer_allowed") and player.round_number >= 3

    @staticmethod
    def after_all_players_arrive(group):
        players = group.get_players()
        for player in players:
            total_in = 0
            for other in players:
                if other.id_in_group == player.id_in_group:
                    continue
                field_name = f"power_transfer_p{player.id_in_group}"
                total_in += getattr(other, field_name, 0) or 0
            player.power_transfer_in_total = round(total_in, 3)
            player.punishment_power_after = max(
                0,
                round(
                    player.punishment_power_before
                    - player.power_transfer_out_total
                    + player.power_transfer_in_total,
                    3,
                ),
            )
            player.participant.vars["punishment_power"] = player.punishment_power_after

            # Carry over the updated punishment power to the next round so that
            # the transfer results persist. creating_session runs before the
            # experiment starts, meaning the defaults written there (1.0) need
            # to be replaced once we know the actual outcome of this round.
            if player.round_number < Constants.num_rounds:
                next_player = player.in_round(player.round_number + 1)
                next_player.punishment_power_before = player.punishment_power_after
                next_player.punishment_power_after = player.punishment_power_after
                next_player.participant.vars["punishment_power"] = player.punishment_power_after

            endowment = player.session.config.get('endowment', Constants.endowment)
            cost_value = float(player.power_transfer_cost or 0)
            remaining = max(0, endowment - cost_value)
            player.available_endowment = c(remaining)

            if player.session.config.get('costly_punishment_transfer') and cost_value > 0:
                player.can_receive_punishment = False
            else:
                player.can_receive_punishment = True

    @staticmethod
    def vars_for_template(player):
        players = player.group.get_players()
        current_round = player.round_number
        submitted = sum(
            1
            for p in players
            if p.participant.vars.get('power_transfer_submitted_round') == current_round
        )
        total = len(players)
        return dict(waiting_progress=submitted, waiting_total=total)


class PowerTransferResult(Page):
    @staticmethod
    def is_displayed(player):
        session = player.session
        return session.config.get("power_transfer_allowed") and player.round_number >= 3

    @staticmethod
    def vars_for_template(player):
        session = player.session
        group_players = sorted(
            player.group.get_players(), key=lambda p: p.id_in_group
        )

        columns = []
        for member in group_players:
            transfer_cost_value = member.power_transfer_cost
            if transfer_cost_value is None:
                transfer_cost_display = "0.0"
            else:
                transfer_cost_display = f"{float(transfer_cost_value):.1f}"
            columns.append(
                dict(
                    id_in_group=member.id_in_group,
                    is_self=member.id_in_group == player.id_in_group,
                    header=f"プレイヤー {member.id_in_group}",
                    final_power_display=f"{member.punishment_power_after:.1f} / 1.0",
                    net_transfer_display=f"- {member.power_transfer_out_total:.1f} / + {member.power_transfer_in_total:.1f}",
                    transfer_cost_display=transfer_cost_display,
                    current_balance_display="-",
                )
            )

        transfer_matrix = []
        for giver in group_players:
            row_cells = []
            for receiver in group_players:
                if giver.id_in_group == receiver.id_in_group:
                    row_cells.append(dict(is_self=True, highlight=False, display="-"))
                else:
                    field_name = f"power_transfer_p{receiver.id_in_group}"
                    amount = getattr(giver, field_name, 0) or 0
                    row_cells.append(
                        dict(
                            is_self=False,
                            highlight=receiver.id_in_group == player.id_in_group,
                            display=f"{amount:.1f}",
                        )
                    )
            transfer_matrix.append(
                dict(
                    row_label=f"プレイヤー {giver.id_in_group}",
                    is_self=giver.id_in_group == player.id_in_group,
                    cells=row_cells,
                )
            )

        headers = [
            "あなたへの転移" if p.id_in_group == player.id_in_group else f"プレイヤー {p.id_in_group} への転移"
            for p in group_players
        ]
        columns_length = len(columns)

        return dict(
            columns=columns,
            columns_length=columns_length,
            columns_length_plus_one=columns_length + 1,
            transfer_matrix=transfer_matrix,
            transfer_headers=headers,
            round_number=player.round_number,
            is_costly=session.config.get("costly_punishment_transfer", False),
        )



# =============================================================================
# CLASS: Punishment
# =============================================================================
class Punishment(Page):
    form_model = 'player'

    @staticmethod
    def get_form_fields(player):
        fields = []
        group = player.group
        for i in range(1, Constants.players_per_group + 1):
            if i == player.id_in_group:
                continue
            target = group.get_player_by_id(i)
            if target.can_receive_punishment:
                fields.append(f'punish_p{i}')
        return fields

    @staticmethod
    def is_displayed(player):
        return player.round_number > 1

    @staticmethod
    def vars_for_template(player):
        id_range = list(range(1, Constants.players_per_group + 1))
        endowment = player.session.config['endowment']
        contribution = player.contribution if hasattr(player, 'contribution') else 0

        remaining_mu = endowment - contribution

        return dict(
            players_contribution=player.group.get_players(),
            deduction_points=player.session.config['deduction_points'],
            id_range=id_range,
            history_rounds=build_history_rounds(player),
            can_receive_map={p.id_in_group: p.can_receive_punishment for p in player.group.get_players()},
            remaining_mu = remaining_mu
        )

    @staticmethod
    def error_message(player, values):
        total_punishment = 0
        for i in range(1, Constants.players_per_group + 1):
            field_name = f'punish_p{i}'
            if field_name in values and values[field_name] is not None:
                total_punishment += values[field_name]

        if total_punishment > player.session.config['deduction_points']:
            return f"送られた点数 {player.session.config['deduction_points']}　を越えてはいけません。"
        punishment_cost = player.session.config.get('punishment_cost', 1)
        total_cost = total_punishment * punishment_cost
        available = float(player.available_endowment or 0)
        if total_cost > available + 1e-6:
            if punishment_cost > 0:
                max_points = int(available // punishment_cost)
            else:
                max_points = total_punishment
            return f"現在、使えるMUsは {max_points} です。もう一度試して下さい。"

    @staticmethod
    def before_next_page(player, timeout_happened):
        punishment_cost = player.session.config.get('punishment_cost', 1)
        total_punishment = 0
        for i in range(1, Constants.players_per_group + 1):
            field_name = f'punish_p{i}'
            if hasattr(player, field_name):
                value = getattr(player, field_name, 0) or 0
                total_punishment += value
        total_cost = c(total_punishment * punishment_cost)
        player.available_before_punishment = player.available_endowment or c(0)
        player.attempted_punishment_cost = total_cost
        player.attempted_punishment_points = total_punishment
        player.participant.vars['punishment_submitted_round'] = player.round_number

# =============================================================================
# CLASS: PunishmentWaitPage
# =============================================================================
class PunishmentWaitPage(WaitPage):
    template_name = "game/PunishmentWait.html"

    @staticmethod
    def is_displayed(player):
        return player.round_number > 1

    @staticmethod
    def after_all_players_arrive(group):
        group.set_payoff()

    @staticmethod
    def vars_for_template(player):
        players = player.group.get_players()
        current_round = player.round_number
        submitted = sum(
            1
            for p in players
            if p.participant.vars.get('punishment_submitted_round') == current_round
        )
        total = len(players)
        return dict(waiting_progress=submitted, waiting_total=total)

# =============================================================================
# CLASS: RoundResult
# =============================================================================
class RoundResult(Page):
    @staticmethod
    def is_displayed(player):
        return player.round_number > 1

    @staticmethod
    def vars_for_template(player):
        session = player.session
        treatment_name = session.config.get('treatment_name', 'fixed')
        show_power_transfer = (
            session.config.get('power_transfer_allowed')
            and player.round_number >= 3
        )

        endowment = session.config['endowment']
        deduction_points = session.config['deduction_points']
        endowment_currency = c(endowment)
        share = player.group.individual_share

        cumulative_payoff = player.participant.vars.get('cumulative_payoff', c(0))
        payoff_from_contribution = endowment_currency - player.contribution + share

        players = sorted(player.group.get_players(), key=lambda p: p.id_in_group)

        players_map = {}
        for member in players:
            players_map[member.id_in_group] = dict(
                id_in_group=member.id_in_group,
                contribution=member.contribution,
                endowment=endowment_currency,
                punishment_sent_total=0,
                punishment_received_total=0,
                power_before=member.punishment_power_before,
                power_after=member.punishment_power_after,
                power_after_display=f"{member.punishment_power_after:.1f}",
                power_transfer_out=member.power_transfer_out_total,
                power_transfer_in=member.power_transfer_in_total,
                power_transfer_out_display=f"{member.power_transfer_out_total:.1f}",
                power_transfer_in_display=f"{member.power_transfer_in_total:.1f}",
                power_transfer_cost=member.power_transfer_cost,
                available_endowment=member.available_endowment,
                available_before_contribution=member.available_before_contribution or (member.available_endowment or c(0)) + member.contribution,
            )

        for member in players:
            total_sent = getattr(member, 'punishment_points_given_actual', None)
            if total_sent is None:
                total_sent = 0
                for other in players:
                    if other.id_in_group == member.id_in_group:
                        continue
                    field_name = f'punish_p{other.id_in_group}'
                    total_sent += getattr(member, field_name, 0) or 0
            players_map[member.id_in_group]['punishment_sent_total'] = total_sent

        effectiveness_base = session.config.get('power_effectiveness', Constants.power_effectiveness)
        matrix_rows = []
        for victim in players:
            actual_loss = float(victim.punishment_received or 0)
            if actual_loss <= 0:
                victim_before = float(victim.available_before_punishment or victim.available_endowment or 0)
                victim_after = float(victim.available_endowment or 0)
                diff = victim_before - victim_after
                if diff > actual_loss:
                    actual_loss = max(0.0, diff)

            attempted_loss = 0.0
            attempted_points = {}
            effective_power_map = {}
            for giver in players:
                if giver.id_in_group == victim.id_in_group:
                    continue
                points = getattr(giver, f'punish_p{victim.id_in_group}', 0) or 0
                attempted_points[giver.id_in_group] = points
                effective_power = (
                    giver.punishment_power_after
                    or giver.participant.vars.get('punishment_power', 1.0)
                )
                effective_power_map[giver.id_in_group] = effective_power
                if points > 0:
                    attempted_loss += points * effectiveness_base * effective_power

            if attempted_loss <= 0:
                scale = 0.0
            else:
                scale = min(1.0, actual_loss / attempted_loss)

            cells = []
            total_received = 0.0
            for giver in players:
                is_self = giver.id_in_group == victim.id_in_group
                if is_self:
                    cells.append(dict(is_self=True, amount=None, amount_display=None))
                else:
                    points_attempted = attempted_points.get(giver.id_in_group, 0)
                    points_used = round(points_attempted * scale, 6)
                    effective_power = effective_power_map.get(
                        giver.id_in_group,
                        giver.punishment_power_after
                        or giver.participant.vars.get('punishment_power', 1.0),
                    )
                    actual_loss_value = points_used * effectiveness_base * effective_power
                    total_received += actual_loss_value
                    loss_display = c(actual_loss_value)
                    cells.append(
                        dict(
                            is_self=False,
                            amount=loss_display,
                            amount_display=loss_display,
                        )
                    )

            if victim.punishment_received is not None:
                summary_loss = victim.punishment_received
            else:
                summary_loss = c(total_received)

            players_map[victim.id_in_group]['punishment_received_total'] = summary_loss
            matrix_rows.append(dict(victim_id=victim.id_in_group, cells=cells))

        players_summary = [players_map[idx] for idx in sorted(players_map.keys())]

        return dict(
            payoff_from_contribution=payoff_from_contribution,
            cumulative_payoff=cumulative_payoff,
            players_summary=players_summary,
            matrix_rows=matrix_rows,
            matrix_headers=[member.id_in_group for member in players],
            show_power_transfer=show_power_transfer,
            treatment_name=treatment_name,
            deduction_points=deduction_points,
            endowment=endowment_currency,
        )

    @staticmethod
    def before_next_page(player, timeout_happened):
        stop_round = player.session.config.get('browser_bot_stop_round')
        if (
            stop_round
            and player.round_number == stop_round
            and player.participant.is_browser_bot
        ):
            player.participant.is_browser_bot = False

# =============================================================================
# CLASS: FinalResult (ゲームアプリ内の最終ページ)
# =============================================================================
class FinalResult(Page):
    @staticmethod
    def is_displayed(player):
        return player.round_number == Constants.num_rounds

    @staticmethod
    def vars_for_template(player):
        final_payoff_jpy = player.participant.payoff_plus_participation_fee()
        performance_payoff = player.participant.payoff.to_real_world_currency(player.session)
        currency_code = player.session.config.get('real_world_currency_code', 'JPY')

        return {
            'players': sorted(player.group.get_players(), key=lambda p: p.id_in_group),
            'final_payoff_jpy': final_payoff_jpy,
            'C': Constants,
            'Constants': Constants,
            'performance_payoff': performance_payoff,
            'currency_code': currency_code,
        }


# =============================================================================
# ページの表示順
# =============================================================================
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
    FinalResult, # <--- ゲームアプリの最後に表示する最終結果ページ
]
