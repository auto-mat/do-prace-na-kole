from sitetree.utils import item, tree

sitetrees = (
    tree(
        'maintree', 'Hlavní menu', items=[
            item('Zapsat jízdu!', 'profil', title_en='Enter ride!'),
            item(
                'Profil', 'edit_profile_detailed', title_en='Profile', children=[
                    item('Změnit heslo', 'password_change', title_en='Change password'),
                    item('Změnit tým', 'zmenit_tym', title_en='Change team'),
                    item('Změnit triko', 'zmenit_triko', title_en='Change t-shirt'),
                    item('Platba', 'typ_platby', title_en='Payment'),
                ],
            ),
            item('Tým', 'team_members', title_en='Team'),
            item(
                'Výsledky', 'other_team_members_results', title_en='Results', children=[
                    item('Pravidelnostní soutěže', 'competitions', title_en='Regularity competitions'),
                    item('Výkonnostní soutěže', 'length_competitions', title_en='Performance competitions'),
                    item('Ostatní', 'questionnaire_competitions', title_en='Other'),
                ],
            ),
        ],
    ),
    tree(
        'maintree_vyzva', 'Hlavní menu - výzvy', items=[
            item('Zapsat jízdu!', 'profil', title_en='Enter ride!'),
            item(
                'Profil', 'edit_profile_detailed', title_en='Profile', children=[
                    item('Změnit heslo', 'password_change', title_en='Change password'),
                    item('Změnit společnost', 'zmenit_tym', title_en='Change company'),
                ],
            ),
            item(
                'Výsledky', 'competitions', title_en='Results', children=[
                    item('Pravidelnostní soutěže', 'competitions', title_en='Regularity competitions'),
                    item('Výkonnostní soutěže', 'length_competitions', title_en='Performance competitions'),
                    item('Ostatní', 'questionnaire_competitions', title_en='Other'),
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
            item('Odhlásit', 'logout', title_en='Logout'),
            item(
                'O nás', 'https://www.auto-mat.cz/', title_en='About us', children=[
                    item('O Auto*Matu', 'https://www.auto-mat.cz/', title_en='About Auto*Mat', url_as_pattern=False),
                    item('Podpořte Auto*Mat', 'https://www.nakrmteautomat.cz/', title_en='Support Auto*Mat', url_as_pattern=False),
                    item('Svobodný Software', 'https://github.com/auto-mat/do-prace-na-kole', title_en='Free software', url_as_pattern=False),
                ],
            ),
        ],
    ),
    tree(
        'unlogged_menu', 'Menu pro nezalogované', items=[
            item('Přihlásit', 'login', title_en='Login'),
            item('Registrovat', 'registration_access', title_en='Register'),
            item('Registrovat firemního koordinátora', 'logout', title_en='Register company coordinator'),
            item('Zapomenuté heslo', 'password_reset', title_en='Forgotten password'),
        ],
    ),
    tree(
        'company_coordinator_menu', 'Menu firemního koordinátora', items=[
            item(
                'Firemní koordinátor', 'company_admin_pay_for_users', title_en='Company coordinator', children=[
                    item('Společnost', 'company_structure'),
                    item('Adresa společnosti', 'edit_company'),
                    item('Startovné', 'company_admin_pay_for_users'),
                    item('Faktury', 'invoices'),
                    item('Soutěže', 'company_admin_related_competitions'),
                    item('Firemní soutěže', 'company_admin_competitions'),
                    item('Vypsat soutěž', 'company_admin_competition'),
                ],
            ),
        ],
    ),
)
