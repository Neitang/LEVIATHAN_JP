# introduction/models.py
from otree.api import (
    models, BaseConstants, BaseSubsession, BaseGroup, BasePlayer, Currency as c
)

class Constants(BaseConstants):
    name_in_url = 'introduction'
    players_per_group = None 
    num_rounds = 1 

class Subsession(BaseSubsession):
    pass

class Group(BaseGroup):
    pass

class Player(BasePlayer):
    q1_fixed = models.IntegerField(label="問題1：初期保有額はいくらですか？", min=0)
    q2_fixed = models.FloatField(label="問題2：公共プールの乗数はいくつですか？", min=0)

    q2_transfer_free = models.FloatField(label="問題1：移譲にかかるコストはいくらですか？", min=0)
    q3_transfer_free = models.IntegerField(label="問題2：最大で何ポイントまで移譲できますか？", min=0)

    q1_transfer_cost = models.FloatField(label="問題2：移譲コスト率はいくつですか？", min=0)
    q2_transfer_cost = models.StringField(
        label="問題1：罰威力を移譲するとコストを支払う必要がありますか？",
        choices=[('yes', 'はい'), ('no', 'いいえ')]
    )
