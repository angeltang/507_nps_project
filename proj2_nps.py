#################################
##### Name: Angel Tang
##### Uniqname: rongtang
#################################

import bs4
from bs4 import BeautifulSoup
import requests
import json
import secrets # file that contains your API key

NPS_API_KEY = secrets.NPS_API_KEY
MAP_API_CONSUMER_KEY = secrets.MAP_API_CONSUMER_KEY
MAP_API_CONSUMER_SECRET = secrets.MAP_API_CONSUMER_SECRET
CACHE_FILENAME = "cache.json"

def open_cache():
    ''' opens the cache file if it exists and loads the JSON into
    a dictionary, which it then returns.
    if the cache file doesn't exist, creates a new cache dictionary
    Parameters
    ----------
    None
    Returns
    -------
    The opened cache
    '''
    try:
        cache_file = open(CACHE_FILENAME, 'r')
        cache_contents = cache_file.read()
        cache_dict = json.loads(cache_contents)
        cache_file.close()
    except:
        cache_dict = {}
    return cache_dict

def save_cache(cache_dict):
    ''' saves the current state of the cache to disk
    Parameters
    ----------
    cache_dict: dict
        The dictionary to save
    Returns
    -------
    None
    '''
    dumped_json_cache = json.dumps(cache_dict)
    fw = open(CACHE_FILENAME,"w")
    fw.write(dumped_json_cache)
    fw.close()

SITE_CACHE = open_cache()

class NationalSite:
    '''a national site

    Instance Attributes
    -------------------
    category: string
        the category of a national site (e.g. 'National Park', '')
        some sites have blank category.

    name: string
        the name of a national site (e.g. 'Isle Royale')

    address: string
        the city and state of a national site (e.g. 'Houghton, MI')

    zipcode: string
        the zip-code of a national site (e.g. '49931', '82190-0168')

    phone: string
        the phone of a national site (e.g. '(616) 319-7906', '307-344-7381')
    '''
    def __init__(self, category, name, address, zipcode, phone):
        self.category = category
        self.name = name
        self.address = address
        self.zipcode = zipcode
        self.phone = phone

    def info(self):
        return f'{self.name} ({self.category}): {self.address} {self.zipcode}'


def build_state_url_dict():
    ''' Make a dictionary that maps state name to state page url from
    "https://www.nps.gov"

    Parameters
    ----------
    None

    Returns
    -------
    dict
        key is a state name and value is the url
        e.g. {'michigan':'https://www.nps.gov/state/mi/index.htm', ...}
    '''
    base_url = 'https://www.nps.gov'
    html = requests.get(base_url).text
    soup = BeautifulSoup(html, 'html.parser')
    search_div = soup.find(class_='dropdown-menu SearchBar-keywordSearch')
    states = search_div.find_all('a')
    # print(search_div) ### test
    # print(states) ### test
    state_url_dict = {}
    for state in states:
        # print(state.string) # this is the state name without the url
        # print(state['href']) # the link
        state_url_dict[state.string.lower()] = base_url + state['href']

    # print(state_url_dict)
    # type(state_url_dict)
    return state_url_dict

def get_site_instance(site_url):
    '''Make an instances from a national site URL.

    Parameters
    ----------
    site_url: string
        The URL for a national site page in nps.gov

    Returns
    -------
    instance
        a national site instance
    '''

    if site_url in SITE_CACHE:
        print('Using Cache')
        category = SITE_CACHE[site_url]['category']
        name = SITE_CACHE[site_url]['name']
        address = SITE_CACHE[site_url]['address']
        zipcode = SITE_CACHE[site_url]['zipcode']
        phone = SITE_CACHE[site_url]['phone']

    else:
        print('Fetching')
        # html = requests.get('https://www.nps.gov/noco/index.htm').text ### test
        # print(site_url)
        html = requests.get(site_url).text
        soup = BeautifulSoup(html, 'html.parser')
        # print(soup.prettify())

        hero = soup.find(class_='Hero-titleContainer clearfix')
        name = hero.find('a').string
        # print(name)

        category = soup.find(class_='Hero-designation').string
        # print(f'{name} ({category})')


        #address
        try:
            city = soup.find(itemprop='addressLocality').string
        except: city = ''

        try:
            state = soup.find(itemprop='addressRegion').string
        except: state = ''

        address = f'{city}, {state}'
        # print(address)

        #zipcode
        try:
            zipcode = soup.find(itemprop='postalCode').string.strip()
        except: zipcode = ''
        # print(zipcode)

        #phone
        phone = soup.find(class_='tel').string.strip()
        # print(phone)

        #build cache
        SITE_CACHE[site_url] = {}
        SITE_CACHE[site_url]['category'] = category
        SITE_CACHE[site_url]['name'] = name
        SITE_CACHE[site_url]['address'] = address
        SITE_CACHE[site_url]['zipcode'] = zipcode
        SITE_CACHE[site_url]['phone'] = phone
        save_cache(SITE_CACHE)

    return NationalSite(category, name, address, zipcode, phone)


def get_sites_for_state(state_url):
    '''Make a list of national site instances from a state URL.

    Parameters
    ----------
    state_url: string
        The URL for a state page in nps.gov

    Returns
    -------
    list
        a list of national site instances
    '''
    # state_url='https://www.nps.gov/state/az/index.htm' ### test

    base_url = 'https://www.nps.gov'
    sites = []
    sites_url = []

    if state_url in SITE_CACHE:
        print('Using Cache')
        sites_url = SITE_CACHE[state_url]
        for site_url in sites_url:
            park = get_site_instance(site_url)
            sites.append(park)

    else:
        print('Fetching')
        html = requests.get(state_url).text
        soup = BeautifulSoup(html, 'html.parser')
        h3 = soup.find_all('h3')
        # print(h3)
        for result in h3:
            park_url_raw = result.find('a')
            if park_url_raw:
                park_url = base_url + park_url_raw['href']
                # print(park_url) ### test
                park = get_site_instance(park_url)
                sites.append(park)

                # cache
                # site = {
                #     'category': park.category,
                #     'name': park.name,
                #     'address': park.address,
                #     'zipcode': park.zipcode,
                #     'phone': park.phone,
                # }
                sites_url.append(park_url)
        SITE_CACHE[state_url] = sites_url
        save_cache(SITE_CACHE)

    return sites

def get_nearby_places(site_object):
    '''Obtain API data from MapQuest API.

    Parameters
    ----------
    site_object: object
        an instance of a national site

    Returns
    -------
    dict
        a converted API return from MapQuest API
    '''
    base_url = 'http://www.mapquestapi.com/search/v2/radius'

    origin = site_object.zipcode

    if origin in SITE_CACHE:
        print('Using Cache')
        results_json = SITE_CACHE[origin]
    else:
        print('Fetching')
        # key, origin, radius, maxMatches, ambiguities, outFormat
        key = MAP_API_CONSUMER_KEY
        radius = 10 # 10 miles
        units = 'm'
        maxMatches = 10
        ambiguities = 'ignore'
        outFormat = 'json'
        # construct call
        map_url = base_url + f'?key={key}&origin={origin}&radius={radius}&units={units}&maxMatches={maxMatches}&ambiguities={ambiguities}&outFormat={outFormat}'
        # print(map_url) ### test

        ### test
        # http://www.mapquestapi.com/search/v2/radius?key=Y5CzQkUP3DtY7szWSL3TGO9te5VdPNyq&origin=49630&radius=10&units=m&maxMatches=10&ambiguities=ignore&outFormat=json

        # accessapi
        response = requests.get(map_url)
        json_str = response.text
        results_json = json.loads(json_str)
        # results_json = results_json['searchResults']

        SITE_CACHE[origin] = results_json
        save_cache(SITE_CACHE)

    print_nearby_sites(results_json)

    return results_json

def print_header(state):
    header = f'''
-----------------------------------------
List of National Sites in {state.title()}
-----------------------------------------
'''
    print(header)
    return

def print_sites(sites):
    for i,site in enumerate(sites):
        print(f'[{i+1}] {site.info()}')
    print('-----------------------------------------')
    return

def print_state_info(state, sites):
    print_header(state)
    print_sites(sites)
    detail_search(sites)
    return

def print_nearby_sites(results_json):

    sites = results_json['searchResults']
    here = results_json['origin']['postalCode']
    header = f'''
-----------------------------------------
List of nearby sites to {here}
-----------------------------------------
'''
    print(header)
    # print(f'List of nearby sites to {here}: ')

    for site in sites:
        name = site['name']

        category = site['fields']['group_sic_code_name_ext']
        if category == '':
            category = 'no category'

        address = site['fields']['address']
        if address == '':
            address = 'no address'

        city = site['fields']['city']
        if city == '':
            city = 'no city'

        print(f'- {name} ({category}): {address}, {city}')

    print('-----------------------------------------')

    return

def ask():
    user_state = input('Enter a state name (e.g. Michigan, michigan) or "exit": ')
    state = user_state.lower().strip()
    if user_state == 'exit':
        exit()
    elif user_state in state_url_dict:
        state_url = state_url_dict[user_state]
        sites = get_sites_for_state(state_url)
        print_state_info(state, sites)
        ask()
        return
    else:
        print('Please enter a valid state name in the U.S.')
        ask()
        return

def retrieve_site_instance(index, sites):
    total = len(sites)
    try:
        i = int(index) - 1
        if i <= total and i > 0:
            get_nearby_places(sites[i])
            return
        else:
            print(f'Please enter a valid interger from 1 to {total}.')
            detail_search(sites)
            return
    except:
        print(f'Please enter a valid interger from 1 to {total}.')
        detail_search(sites)
        return

def detail_search(sites):
    index = input('Choose the number for detail search or "exit" or "back": ')
    index = index.lower().strip()
    if index == 'exit':
        exit()
    elif index == 'back':
        ask()
        return
    else:
        retrieve_site_instance(index, sites)
        return

state_url_dict = build_state_url_dict()

if __name__ == "__main__":
    SITE_CACHE = open_cache()
    get_site_instance('https://www.nps.gov/yose/index.htm')
    ask()