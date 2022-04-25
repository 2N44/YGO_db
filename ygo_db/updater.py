import os
import scraping as scrap
import languages as lang
from bs4 import BeautifulSoup

LANGUAGE = [
    lang.English(),
    lang.French(),
    lang.German(),
    lang.Spanich(),
    lang.Italian(),
    lang.Portuguese()
]

def add_set_data(card_data_scraped, card_data_db, lan):

    for card_set in card_data_scraped['sets']:

        set_code = card_set['set_code']
        rarity_code = lan.rar_dict[card_set['rarity']]
        card_code = dict()
        card_code[lan.language] = card_set['card_code']
        rarity = dict()
        rarity[lan.language] = card_set['rarity']
        found = False

        for set_idx in range(len(card_data_db['sets'])):

            set_info = card_data_db['sets'][set_idx]

            if set_info['set_code']==set_code and set_info['rarity_code']==rarity_code:

                set_info['set_name'][lan.language] = card_set['set_name']
                set_info['card_code'][lan.language] = card_set['card_code']
                set_info['rarity'][lan.language] = card_set['rarity']
                card_data_db['sets'][set_idx] = set_info
                found = True

        if not found:

            set_info = {
                'set_code': set_code,
                'set_name': {lan.language: card_set['set_name']},
                'date': card_set['date'],
                'card_code': card_code,
                'rarity': rarity,
                'rarity_code': rarity_code,
                'artwork': 0,
            }
            card_data_db['sets'].append(set_info)

    return card_data_db

def add_product(pid, database):

    id_list = scrap.get_card_in_set(pid)


    for konami_id in id_list:

        result = database.search(tinydb.Query().konami_id==konami_id)
        card_info = {
            'name': {},
            'attribute': {},
            'type': {},
            'race': {},
            'sets': [],
            'pendulum_effect': {},
            'desc': {},
        }

        if 'atk' in card_info_lang:

            card_info['atk'] = card_info_lang['atk']

        if 'def' in card_info_lang:

            card_info['def'] = card_info_lang['def']

        if 'level' in card_info_lang:

            card_info['level'] = card_info_lang['level']

        if 'rank' in card_info_lang:

            card_info['rank'] = card_info_lang['rank']

        if 'scale' in card_info_lang:

            card_info['scale'] = card_info_lang['scale']

        if 'link' in card_info_lang:

            card_info['link'] = card_info_lang['link']

        for lan in LANGUAGE:

            card_info_lang = scrap.get_full_page(konami_id, lan)

            if len(result)==1:

                card_info = add_set_data(card_info_lang, result[0], lan)                
                database.update({'sets': card_info['sets']}, tinydb.Query().konami_id==konami_id)

            elif len(result) < 1:

                card_info['name'][lan.language] = card_info_lang['name']
                card_info['type'][lan.language] = card_info_lang['type']
                card_info['race'][lan.language] = card_info_lang['race']
                card_info['desc'][lan.language] = card_info_lang['desc']

                if 'pendulum_effect' in card_info:

                    card_info['pendulum_effect'][lan.language] = card_info_lang['pendulum_effect']

                if lan.language == 'en':

                    card_more_info = scrap.get_more_data(card_info_lang['name'])

                card_info = add_set_data(card_info_lang, card_info, lan)
                

            else:

                raise DatabaseError(len(result))

        if len(result) < 1:

            database.insert({**card_info, **card_more_info})

def update_card_field(card_id, field, database):

    updated_info = dict()

    for key in field:

            updated_info[key]=dict()

    for lan in LANGUAGE:

        card_info = scrap.get_partial_page(card_id, lan)

        for key in field:

            updated_info[key][lan.language] = card_info[key]

    database.update(updated_info, tinydb.Query().konami_id==card_id)      


class Card():

    def __init__(self, card_soup):

        self.id = card_soup.text
        self.name = card_soup.name
        self.modified = card_soup.modified
        self.date = None

        if card_soup.date is not None:

            self.date = card_soup.date


class Set():

    def __init__(self, set_soup):

        self.name = set_soup.name
        self.type = set_soup.type
        self.pid = set_soup.text
        self.date = None

        if set_soup.date is not None:

            self.date = set_soup.date


class Version():

    def __init__(self, version_soup):

        self.date = version_soup.date
        self.id = version_soup.id
        self.note = version_soup.note.text
        self.card = []
        self.set = []

        for set_soup in version_soup.find_all('set'):

            self.set.append(Set(set_soup))

        for card_soup in version_soup.find_all('card'):

            self.card.append(Card(card_soup))


class Release():

    def __init__(self, path):

        with open(path, 'r') as f:

            text = ''.join(f.readlines())

        soup = BeautifulSoup(text, 'html_parser')
        self.release = []

        for version_soup in soup.find_all('version'):

            self.release.append(Version(version_soup))

        self.version = self.release[0]


class UpdaterDB():

    def __init__(self, database, path_version=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'database', 'db_version.txt'), path_release_history=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'database', 'db_release.html')):

        self.database = database
        with open(path_version, 'r') as f:

            self.current_version = f.read()[1:]

        scrap.get_new_version_release(path_release_history)
        self.release_history = Release(path_release_history)
        self.last_release = self.release_history.version.id
        self.release_to_cath_up = []

    def check_db_version(self):

        if self.current_version == self.last_release:

            self.up_to_date = True

            for release in self.release_history.release:

                if release.id == self.current_version:

                    break

                self.release_to_cath_up.append(release)

        else:

            self.up_to_date = False

    def update(self):

        for release in self.release_history.release:

            for sets in release.set:

                add_product(sets.pid, self.database)

            for card in release.card:

                update_card_field(card.id, card.modified.split('/'), self.database)

        with open(path_version, 'w') as f:

            f.write('v'+self.last_release)

        self.current_version = self.last_release

