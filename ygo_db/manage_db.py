import os
import tinydb
import languages
import re
import YgoDBError as error
from tinydb.operations import add
from unidecode import unidecode

LANGUAGE = [
    lang.English(),
    lang.French(),
    lang.German(),
    lang.Spanich(),
    lang.Italian(),
    lang.Portuguese()
]

def _create_card_data(card_code, rarity, condition, number, language=None, edition='reprint', note=None, sleeved=None):

	'''
		Fetch complementary data to enter the database for a card.
	'''

	for lan in LANGUAGE:

		rarity_code = lan.rar_dict[rarity]
		list_info = cards_db.search(tinydb.Query().sets.any((tinydb.Query().card_code[lan.language]==card_code) & (tinydb.Query().rarity_code==rarity_code)))

		if len(list_info)>0:

			break

	all_info = list_info[0]
	card_info = {
		'passcode': all_info['passcode'],
		'name': all_info['name'],
		'set_code': card_code.split('-')[0],
		'card_code': card_code,
		'rarity': rarity,
		'rarity_code': rarity_code,
		'condition': condition,
		'number': number,
		'language': card_code.split('-')[1][:2],
		'edition': edition,
	}

	for card_set in all_info['sets']:

		if card_set['set_code']==card_code.split('-')[0]:

			card_info['rarity_code'] = card_set['rarity_code']
			break

	if note is not None:

		card_info['note'] = note

	if sleeved is not None:

		card_info['sleeved'] = sleeved

	return card_info

class Manager():

	'''
		Manager of your database. Used to select table, insert or update data, search, ...
	'''

	def __init__(self, all_cards_path, my_cards_path):

		self.cards_db = tinydb.TinyDB(all_cards_path)
		self.my_db = tinydb.TinyDB(my_cards_path)
		self.all_cards_path = all_cards_path
		self.my_cards_path = my_cards_path
		self.table = self.my_db

	def select_table(self, name='_default'):

		'''
			Select table in your database by entering a table name.
		'''

		self.table = self.my_db.table(name)

	def insert_card(self, card_code, rarity, condition, number, language=None, edition='reprint', note=None, sleeved=None):

		'''
			Insert a new card in the table.
		'''

		card_info = _create_card_data(card_code, rarity, condition, number, language, edition, note, sleeved)
		self.table.insert(card_info)

	def upsert_card(self, card_code, rarity, condition, number, language=None, edition='reprint', note=None, sleeved=None):

		'''
			Insert a new line in the table or update the number if the line already exists.
		'''

		card_info = _create_card_data(card_code, rarity, condition, number, language, edition, note, sleeved)
		query = tinydb.Query().passcode == card_info['passcode']

		for key, value in card_info.items():

			if key != 'passcode':

				query = (query) & (tinydb.Query()[key]==value)

		result = self.table.search(query)

		if len(result) == 1:

			self.table.update(add('number', card_info['number']), query)

		elif len(result) == 0:

			self.table.insert(card_info)

		else:

			raise error.DatabaseError(len(result))

	def insert_csv(self, path):

		'''
			Read a csv file and enter it in the databass.
		'''

		with open(path, 'r') as f:

			line = f.readlines()

		for data_idx in range(1, len(line)):

			data = line[data_idx].replace('\n', '').split(',')

			for field_idx in range(len(data)):

				if data[field_idx] == '':

					data[field_idx] = None

			upsert_card(data[0], data[1], data[2], data[3], language=data[4], edition=data[5], note=data[6], sleeved=data[7])


	def search_code(self, key_word, **kwargs):

		'''
			Search if a key word match a card code in the database.
			Research can be filtered:
				set_code,
				rarity,
				condition,
				number,
				language,
				edition
		'''

		query = tinydb.Query().card_code.search(key_word)

		for key, value in kwargs.items():

			if key == 'set_code':

				query = (query) & (tinydb.Query().set_code==value)

			if key == 'rarity':

				query = (query) & (tinydb.Query().rarity==value)

			if key == 'rarity_code':

				query = (query) & (tinydb.Query().rarity_code==value)

			if key == 'condition':

				query = (query) & (tinydb.Query().condition==value)

			if key == 'number':

				query = (query) & (tinydb.Query().number>=value)

			if key == 'language':

				query = (query) & (tinydb.Query().language==value)

			if key == 'edition':

				query = (query) & (tinydb.Query().edition==value)

		return self.table.search(query)

	def search_name(self, key_word, **kwargs):

		'''
			Search if a key word match a car name in the database.
			Research can be filtered:
				set_code,
				rarity,
				condition,
				number,
				language,
				edition
		'''

		result_name = []	

		for language_code in language:

			query = tinydb.Query().name[language_code].search(key_word, flags=re.IGNORECASE)

			for key, value in kwargs.items():

				if key == 'set_code':

					query = (query) & (tinydb.Query().set_code==value)

				if key == 'rarity':

					query = (query) & (tinydb.Query().rarity==value)

				if key == 'rarity_code':

					query = (query) & (tinydb.Query().rarity_code==value)

				if key == 'condition':

					query = (query) & (tinydb.Query().condition==value)

				if key == 'number':

					query = (query) & (tinydb.Query().number>=value)

				if key == 'language':

					query = (query) & (tinydb.Query().language==value)

				if key == 'edition':

					query = (query) & (tinydb.Query().edition==value)

			result_name_language = self.table.search(query)
			result_name = result_name + result_name_language

		return result_name

	def search(self, key_word, **kwargs):

		'''
			Search if a key word match a card code or name in the database.
			Research can be filtered:
				set_code,
				rarity,
				condition,
				number,
				language,
				edition
		'''

		return search_name(key_word, **kwargs) + search_code(key_word, **kwargs)

	def simple_search(self, key_word, **kwargs):

		'''
			Search if a key word match a card code or name in the database and concatenate similar result.
			Research can be filtered:
				set_code,
				rarity,
				condition,
				number,
				language,
				edition
		'''

		result_search = search(self, key_word, **kwargs)
		passcode = []
		result = []

		for card in result_search:

			if card['passcode'] in passcode:

				result[passcode.index(card['passcode'])]['number'] += card['number']

			else:

				card_data = {
					'passcode': card['passcode'],
					'name': card['name'],
					'number': card['number']
				}
				passcode.append(card['passcode'])
				result.append(card_data)

		return result

	def show(self, **kwargs):

		'''
			Show the table. Result can be filtered.
		'''

		query = tinydb.Query().number>=0

		for key, value in kwargs.items():

			if key == 'passcode':

				query = (query) & (tinydb.Query().passcode==value)

			if key == 'card_code':

				query = (query) & (tinydb.Query().card_code==value)

			if key == 'set_code':

				query = (query) & (tinydb.Query().set_code==value)

			if key == 'rarity':

				query = (query) & (tinydb.Query().rarity==value)

			if key == 'rarity_code':

				query = (query) & (tinydb.Query().rarity_code==value)

			if key == 'condition':

				query = (query) & (tinydb.Query().condition==value)

			if key == 'number':

				query = (query) & (tinydb.Query().number>=value)

			if key == 'language':

				query = (query) & (tinydb.Query().language==value)

			if key == 'edition':

				query = (query) & (tinydb.Query().edition==value)

		if query == tinydb.Query().number>=0:

			return self.table.all()

		else:

			return self.table.search(query)