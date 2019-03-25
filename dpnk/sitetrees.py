from sitetree.utils import item, tree

sitetrees = (
    tree(
        'maintree', 'Hlavní menu', items=[
            item('Zapsat jízdu!', 'calendar', title_en='Take a Ride!'),
            item(
                'Profil', 'edit_profile_detailed', title_en='Profile', children=[
                    item('Změnit osobní údaje', 'edit_profile_detailed', title_en='Change Personal Details'),
                    item('Změnit tým', 'zmenit_tym', title_en='Change Team'),
                    item('Triko', 'zmenit_triko', title_en='Change T-Shirts'),
                    item('Platba', 'typ_platby', title_en='Payment'),
                    item('Aplikace', 'application', title_en='Applications'),
                ],
            ),
            item('Tým', 'team_members', title_en='Team'),
            item(
                'Výsledky', None, title_en='Results', children=[
                    item('Pravidelnostní soutěže', 'competitions', title_en='Regularity Competitions'),
                    item('Výkonnostní soutěže', 'length_competitions', title_en='Performance Competitions'),
                    item('Ostatní soutěže', 'questionnaire_competitions', title_en='Other Competitions'),
                    item('Minulé ročníky', 'diplomas', title_en='Previous Years'),
                ],
            ),
        ],
    ),
    tree(
        'maintree_vyzva', 'Hlavní menu - výzvy', items=[
            item('Zapsat jízdu!', 'calendar', title_en='Enter ride!'),
            item(
                'Profil', 'edit_profile_detailed', title_en='Profile', children=[
                    item('Změnit společnost', 'zmenit_tym', title_en='Change Company', title_dsnkcs='Změnit školu'),
                    item('Aplikace', 'application', title_en='Applications'),
                ],
            ),
            item(
                'Výsledky', None, title_en='Results', children=[
                    item('Pravidelnostní soutěže', 'competitions', title_en='Regularity Competitions'),
                    item('Výkonnostní soutěže', 'length_competitions', title_en='Performance Competitions'),
                    item('Ostatní soutěže', 'questionnaire_competitions', title_en='Other Competitions'),
                    item('Minulé ročníky', 'diplomas', title_en='Previous Years'),
                ],
            ),
        ],
    ),
    tree(
        'admin_menu', 'Administrace', items=[
            item('Administrace', 'admin:index', title_en='Admininstration'),
        ],
    ),
    tree(
        'about_us', 'O nás', items=[
            item(
                'O nás', 'https://www.auto-mat.cz/', title_en='About us', children=[
                    item('O Auto*Matu', 'https://www.auto-mat.cz/', title_en='About Auto*Mat', url_as_pattern=False),
                    item('Podpořte Auto*Mat', 'https://www.nakrmteautomat.cz/', title_en='Support Auto*Mat', url_as_pattern=False),
                    item('Svobodný Software', 'https://github.com/auto-mat/do-prace-na-kole', title_en='Free Software', url_as_pattern=False),
                ],
            ),
            item('Odhlásit', 'logout', title_en='Logout'),
        ],
    ),
    tree(
        'unlogged_menu', 'Menu pro nezalogované', items=[
            item('Přihlásit', 'login', title_en='Login'),
            item('Registrovat', 'registration_access', title_en='Register'),
            item('Registrovat firemního koordinátora', 'logout', title_en='Register Company Coordinator'),
            item('Zapomenuté heslo', 'password_reset', title_en='Forgotten Password'),
        ],
    ),
    tree(
        'company_coordinator_menu', 'Menu firemního koordinátora', items=[
            item(
                'Firemní koordinátor', None, title_en='Company Coordinator', children=[
                    item('Pobočky', 'company_structure', title_en='Branch Offices'),
                    item('Adresa společnosti', 'edit_company', title_en='Company Address', title_dsnkcs='Adresa školy'),
                    item('Startovné', 'company_admin_pay_for_users', title_en='Participant Fee'),
                    item('Faktury', 'invoices', title_en='Invoices'),
                    item('Soutěže', 'company_admin_related_competitions', title_en='Competitions'),
                    item('Firemní soutěže', 'company_admin_competitions', title_en='Company Competitions'),
                    item('Vypsat soutěž', 'company_admin_competition', title_en='Enroll Competition'),
                ],
            ),
        ],
    ),
)
