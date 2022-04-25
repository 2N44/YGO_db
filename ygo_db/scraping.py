import requests
import json
import languages
import YgoDBError as error
from bs4 import BeautifulSoup


def get_names(names):

	'''
		Get card name.
	'''

	return {'name': names[2]}

def get_unvarialbe_info(item_box, key):

	'''
		Get level/rank/link rate, atk/def, and pendulum scale.
	'''

		card_info = dict()

		for item in item_box:

			item_title = item.span.text.replace('\t','').replace('\r','').replace('\n','')

			if item_title == key['level']:

				card_info['level'] = int(item.find(attrs={'class' : 'item_box_value'}).text.replace(key['level'], ''))

			if item_title == key['rank']:

				card_info['rank'] = int(item.find(attrs={'class' : 'item_box_value'}).text.replace(key['rank'], ''))

			if item_title == key['link']:

				card_info['link'] = int(item.find(attrs={'class' : 'item_box_value'}).text.replace(key['link'], ''))

			if item_title == key['atk']:

				info_str = item.find(attrs={'class' : 'item_box_value'}).text

				if '?' in info_str:

					card_info['atk'] = info_str.replace('\t','').replace('\r','').replace('\n','')

				else:

					card_info['atk'] = int(info_str)

			if item_title == key['atk'] and 'link' not in card_info:

				info_str = item.find(attrs={'class' : 'item_box_value'}).text

				if '?' in info_str:

					card_info['def'] = info_str.replace('\t','').replace('\r','').replace('\n','')

				else:

					card_info['def'] = int(info_str)

			if item_title[:-1] == key['scale']:

				card_info['scale'] = int(item.find(attrs={'class' : 'item_box_value'}).text.replace('\t','').replace('\r','').replace('\n',''))

		return card_info


def get_variable_info(item_box, card_text, sets, key):

	'''
		Get language variating data (attribute, type, race, description, pendulum effect, sets)
	'''

	card_info = dict()

	for item in item_box:

		item_title = item.span.text.replace('\t','').replace('\r','').replace('\n','')

		if item_title == key['attribute']:

			card_info['attribute'] = item.find(attrs={'class' : 'item_box_value'}).text.replace('\t','').replace('\r','').replace('\n','')

		if item.p is not None:

			type_info = item.text.replace('\t','').replace('\r','').replace('\n','').split('/')
			card_info['type'] = '/'.join(type_info[1:])
			card_info['race'] = type_info[0]

		if item_title == key['icon']:

			icon = item.text.replace('\t','').replace('\r','').replace('\n','').replace(item_title,'').split()
			card_info['type'] = icon[1]
			card_info['race'] = icon[0]

	for desc in card_text:

		if desc.div is None:

			card_info['pendulum_effect'] = desc.text.replace('\t','').replace('\r','').replace('\n','')

		else:

			if desc.br is not None:

				#shitty code
				desc = str(desc).replace('<br/>','\n')
				card_info['desc'] = desc.replace('\t','').replace('\r','').replace('\t','').replace(key['description'],'').replace('<div class="item_box_text">\n<div class="text_title">\n\n','').replace('<div class="item_box_title">','').replace('<b></b>','').replace('\n\n\n','').replace('\n\n\n\n','').replace('</div>\n','').replace('</div>','')
		
			else:

				card_info['desc'] = desc.text.replace(desc.div.text,'').replace('\t','').replace('\r','').replace('\n','')

	card_sets = []

	for card_set in sets:

		set_soup = card_set.div
		set_info = {
			'date': set_soup.find(attrs={'class': 'time'}).text.replace('\r', '').replace('\t', '').replace('\n', ''),
			'set_code': set_soup.find(attrs={'class': 'card_number'}).text.replace('\r', '').replace('\t', '').replace('\n', '').split('-')[0],
			'set_name': set_soup.find(attrs={'class': 'pack_name flex_1'}).text.replace('\r', '').replace('\t', '').replace('\n', ''),
			'card_code': set_soup.find(attrs={'class': 'card_number'}).text.replace('\r', '').replace('\t', '').replace('\n', ''),
			'rarity': set_soup.find(attrs={'class': 'icon'}).span.text.replace('\r', '').replace('\t', '').replace('\n', ''),#.replace('竪','è').replace('巽', 'ç'),	#bug on the db.yugioh-card site
			'rarity_code': set_soup.find(attrs={'class': 'icon'}).p.text.replace('\r', '').replace('\t', '').replace('\n', ''),
			'artwork': 0
		} 

		card_sets.append(set_info)

	card_info['sets'] = card_sets

	return card_info


def scrap_webpage(web_id, Language):

	'''
	Scrap a db.yugioh-cards page to get card info
	'''

	url='https://www.db.yugioh-card.com/yugiohdb/card_search.action?ope=2&cid='+str(web_id)+'&request_locale='+Language.language
	#get and parse html
	response = requests.get(url)
	soup = BeautifulSoup(response.text, 'html.parser').article

	if soup is None:

		raise error.RequestError(url, 'URL does not coutain html code.')

	if soup.find(attrs={'class': 'no_data'}) is None:

		#name
		names = soup.div.div.div.h1.text.replace('\t','').replace('\r','').split('\n')
		#characeristics
		item_box = soup.find_all(attrs={'class' : 'item_box'})
		#texts
		card_text = soup.find_all(attrs={'class': 'item_box_text'})
		#sets
		sets = soup.find(attrs={'id': 'update_list'}).find_all(attrs={'class': 't_row'})

		return [names, item_box, card_text, sets]

	else:

		raise error.RequestError(url, 'No data found for this url.')

def get_partial_page(web_id, Language):

	'''
		Scrap URL to get language variating data.
	'''

	card_info = {'konami_id' : web_id}
	web_elements = scrap_webpage(web_id, Language)
	card_info_1 = get_names(web_elements[0])
	card_info_2 = get_variable_info(web_elements[1], web_elements[2], web_elements[3], Language.web_dict)

	return { **card_info, **card_info_1, **card_info_2}

def get_full_page(web_id, Language):

	'''
		Scrap URL to get all data in a given language.
	'''

	card_info = {'konami_id' : web_id}
	web_elements = scrap_webpage(web_id, Language)
	card_info_1 = get_names(web_elements[0])
	card_info_2 = get_unvarialbe_info(web_elements[1], Language.web_dict)		
	card_info_3 = get_variable_info(web_elements[1], web_elements[2], web_elements[3], Language.web_dict)

	return { **card_info, **card_info_1, **card_info_2, **card_info_3}

def get_more_data(card_name):

	'''
		Scrap complementary data from YGOpro API.
	'''
	
	card_name = card_name.replace('#','').replace('%','%25').replace(' & ','_%26_').replace('・','')
	name_url = card_name.replace(' ','%20')
	url = 'https://db.ygoprodeck.com/api/v7/cardinfo.php?name='+name_url
	response = requests.get(url)
	data = json.loads(response.text)

	if 'error' in data:

		raise error.RequestError(url, 'No data found, wrong name.')

	else:

		card_info = data['data'][0]
		add_info_dict = {
			'passcode': card_info['id'],
			'artwork': card_info['card_images'],
		}

		if 'linkmarkers' in card_info:

			add_info_dict['linkmarkers'] = card_info['linkmarkers']

		if 'archetype' in card_info:

			add_info_dict['archetype'] = {'en': card_info['archetype']}

	return add_info_dict

def get_card_in_set(pid):

	'''
		Get card IDs in a set.
	'''

	url= 'https://www.db.yugioh-card.com/yugiohdb/card_search.action?ope=1&pid='+str(pid)+'&mode=1&stype=1&othercon=2&rp=99999&page=1&request_locale=en'
	#get and parse html
	response = requests.get(url)
	soup = BeautifulSoup(response.text, 'html.parser').article

	if soup is None:

		raise error.RequestError(url, 'URL does not coutain html code.')

	if soup.find(attrs={'class': 'no_data'}) is None:

		card_url = soup.find_all(attrs={'class': 'link_value'})
		konami_id = []

		for link in card_url:

			konami_id.append(link['value'].split('=')[-1])

		return konami_id

	else:

		raise error.RequestError(url, 'No data found for this url.')

def get_new_version_release(path):

	'''
		Download release history from github.
	'''

	url = 'https://raw.githubusercontent.com/2N44/YGO_db/main/database/db_release.html'
	response = requests.get(url)

	with open(path, 'w') as f:

		f.write(response.text)