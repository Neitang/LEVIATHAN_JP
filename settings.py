# settings.py
from os import environ

ROOMS = [
    dict(
        name='fixed',
        display_name='罰威力の固定',
        participant_label_file='_rooms/fixed.txt',
        use_secure_urls=True
    ),
    dict(
        name='transfer_free',
        display_name='コストなしの罰威力の移譲',
        participant_label_file='_rooms/transfer_free.txt',
        use_secure_urls=True
    ),
    dict(
        name='transfer_cost',
        display_name='コストありの罰威力の移譲',
        participant_label_file='_rooms/transfer_cost.txt',
        use_secure_urls=True
    ),
]

PARTICIPANT_FIELDS = ["punishment_points_history", "cumulative_payoff"] 
SESSION_FIELDS = ["treatment"]

SESSION_CONFIG_DEFAULTS = dict(
    real_world_currency_per_point=2,
    participation_fee=500,
    doc="公共財ゲーム。Roomsで条件を振り分け。",
    mturk_hit_settings=dict(),
)

SESSION_CONFIGS = [
    dict(
        name='pggp_fixed',
        display_name="公共財ゲーム（罰威力固定）",
        app_sequence=['introduction', 'game', 'survey'], 
        num_demo_participants=5,
        players_per_group=5,
        num_rounds=20,  # ラウンド数
        endowment=20,  # 初期保有額
        contribution_multiplier=1.5,  # 公共財の効率係数
        deduction_points=10,  # 初期罰ポイント
        power_effectiveness=1.0,  # 罰威力
        punishment_cost=1.0, # 罰コスト
        power_transfer_allowed=False,  # 罰威力の移譲不可
        costly_punishment_transfer=False,  # コストなし
        power_transfer_cost_rate=0.0,
        punishment_transfer_unit=0.1,
        practice_rounds=0,
        treatment_name='fixed',
        use_browser_bots=False,
        browser_bot_stop_round=19,
    ),
    dict(
        name='pggp_transfer_free',
        display_name="公共財ゲーム（罰威力移譲・コストなし）",
        app_sequence=['introduction', 'game', 'survey'], 
        num_demo_participants=5,
        players_per_group=5,
        num_rounds=20,  # ラウンド数
        endowment=20,  # 初期保有額
        contribution_multiplier=1.5,  # 公共財の効率係数
        deduction_points=10,  # 初期罰ポイント
        power_effectiveness=1.0,  # 罰威力
        punishment_cost=1.0, # 罰コスト
        power_transfer_allowed=True,  # 罰威力の移譲可
        costly_punishment_transfer=False,  # コストなし
        power_transfer_cost_rate=0.0,
        punishment_transfer_unit=0.1,
        practice_rounds=0,
        treatment_name='transfer_free'
    ),
    dict(
        name='pggp_transfer_cost',
        display_name="公共財ゲーム（罰威力移譲・コストあり）",
        app_sequence=['introduction', 'game', 'survey'], 
        num_demo_participants=5,
        players_per_group=5,
        num_rounds=20,  # ラウンド数
        endowment=20,  # 初期保有額
        contribution_multiplier=1.5,  # 公共財の効率係数
        deduction_points=10,  # 初期罰ポイント
        power_effectiveness=1.0,  # 罰威力
        punishment_cost=1.0, # 罰コスト
        power_transfer_allowed=True,  # 罰威力移譲可
        costly_punishment_transfer=True,  # コストあり
        power_transfer_cost_rate=1.0,
        punishment_transfer_unit=0.1,
        practice_rounds=0,
        treatment_name='transfer_cost'
    ),
]

LANGUAGE_CODE = 'ja'
REAL_WORLD_CURRENCY_CODE = 'JPY'
USE_POINTS = True
TIME_ZONE = "Asia/Tokyo"
POINTS_CUSTOM_NAME = "MUs"
POINTS_DECIMAL_PLACES = 1

ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = environ.get('OTREE_ADMIN_PASSWORD')
SECRET_KEY = 'your-secret-key-here'

DEBUG = True
DEMO_PAGE_INTRO_HTML = """
<p>
    公共財ゲーム
</p>
<p>
    各roomのlinkから、対応する実験条件に参加してください
</p>
<ul>
    <li><a href="/room/fixed">罰威力の固定</a></li>
    <li><a href="/room/transfer_free">コストなしの罰威力の移譲</a></li>
    <li><a href="/room/transfer_cost">コストありの罰威力の移譲</a></li>
</ul>
"""
