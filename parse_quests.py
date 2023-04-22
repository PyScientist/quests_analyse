import random
import time
from requests import Session
import fake_useragent
from bs4 import BeautifulSoup

import logging
logging.basicConfig(
    level=logging.INFO,
    filename='parsing_logging.log',
    format='%(asctime)s -,- %(levelname)s -,- %(name)s -,- %(message)s',
    filemode="a",
)

base_url = 'https://mir-kvestov.ru'
people_rating_url = 'https://mir-kvestov.ru/ratings'


def start_session(proxy_use=False, proxy='socks5://167.71.241.136:33299') -> Session:
    user_agent = fake_useragent.UserAgent().random
    header = {'user-agent': user_agent}
    session_in = Session()
    session_in.headers.update(header)
    if proxy_use:
        proxy_to_use = {'https': proxy}
        session_in.proxies.update(proxy_to_use)
        logging.info(f'Connected with proy: {proxy_to_use}')
    return session_in


def get_main_html(session_in: Session) -> bytes:
    """Function to get content from get request (to the main page) by given Session
    :param session_in: requests session
    :return: content of the page in bytes"""
    try:
        main_html_response = session_in.get(base_url)
        logging.info(f'Got content from the main page: {base_url}')
    except Exception as er:
        main_html_response = ''
        logging.critical('For a some reason main page is no loaded')
        logging.error(er, exc_info=False)
    return main_html_response.content


def get_people_rating(session_in: Session) -> bytes:
    """Function to get content from get request  (to the people rating page) by given Session
    :param session_in: requests session
    :return: content of the page in bytes"""
    try:
        people_rating_html_response = session_in.get(people_rating_url)
        logging.info(f'Got content from people rating page: {base_url}')
    except Exception as er:
        people_rating_html_response = ''
        logging.info(f'For a some reason people rating page is not loaded')
        logging.error(er, exc_info=False)
    return people_rating_html_response.content


def parse_main_page(response) -> dict:
    """Parsing of main page of quests site
    :param: response - result of get request from the main page
    :return quests_dict: it is the dict with keys are href and values are nested dicts
    with keys are (quest_position, quest_type, quest_name, quest_link, quest_rating)"""
    quests_dict = {}
    if response == '':
        logging.critical(f'There is no data for parsing main page')
        return quests_dict
    try:
        soup = BeautifulSoup(response, 'lxml')
        main_page_quests_ul = soup.find('ul', class_='quest-tiles columns-3 quests quests-popular')
        main_page_quests_list = main_page_quests_ul.find_all('li', class_='quest-tile-1')
        for i, quest in enumerate(main_page_quests_list):
            href = quest.find('a', class_='quest_tile_name_link')['href']
            quests_dict[href] = {}
            quests_dict[href]['quest_position'] = f'{i + 1}'
            quests_dict[href]['quest_type'] = quest.find('span', class_='game-type').text
            quests_dict[href]['quest_name'] = quest.find('h4', class_='quest-tile-1__title').text
            quests_dict[href]['quest_link'] = href
            quests_dict[href]['quest_rating'] = quest.find('span', class_='nobr'). \
                text.replace('(', '').replace(')', '').replace(' ', '')
        logging.info('The main page successfully parsed')
    except Exception as er:
        logging.error(er, exc_info=False)
    return quests_dict


def parse_people_rating(response) -> dict:
    """Parsing of main page of quests site
    :param: response - result of get request from the main page
    :return people_rating_dict: it is the dict with keys are href and values are nested dicts
    with keys are (id_people_rating, people_rating, quest_type, quest_name, teams_ammount_for_rating, quest_link)"""
    people_rating_dict = {}
    if response == '':
        logging.critical(f'There is no data for parsing people rating page')
        return people_rating_dict
    soup = BeautifulSoup(response, 'lxml')
    rating_table = soup.find('ul', class_='rating-table-1').find_all('li')
    for i, item in enumerate(rating_table):
        href = item.find('a', class_='quest-5__illustration')['href']
        people_rating_dict[href] = {}
        people_rating_dict[href]['id_people_rating'] = f'{i + 1}'
        people_rating_dict[href]['people_rating'] = item.find('span', class_='quest-5__rating-populi__value').text
        people_rating_dict[href]['quest_type'] = item.find('span', class_='quest-5__game-type').text
        people_rating_dict[href]['quest_name'] = item.find('h4', class_='quest-5__title').text
        people_rating_dict[href]['teams_ammount_for_rating'] = item.find('span', class_='quest-5__commands').text. \
            replace('команд', '').replace('команды', '').replace('команда', '').replace('(', '').replace(')', '').\
            replace('\xa0', '').replace('а', '').replace('ы', '').strip()
        people_rating_dict[href]['quest_link'] = item.find('a', class_='quest-5__illustration')['href']
    return people_rating_dict


def parse_quest_page(response) -> dict:
    """Parsing of single quest page
    :param: response - result of get request from the quest page
    :return quest_dict: it is the dict with keys are
    (people_rating, teams_ammount, avg_mark, ammount_of_votes, *ammount_of_trusted_votes)"""
    quest_details_dict = {}
    if response == '':
        logging.critical(f'There is no data for parsing quest page')
        return quest_details_dict
    soup = BeautifulSoup(response, 'lxml')
    try:
        quest_details_dict['people_rating'] = soup.find('span', class_='quest-rating-populi__value-figure').text
    except AttributeError:
        quest_details_dict['people_rating'] = ''
    try:
        quest_details_dict['teams_ammount'] = soup.find('span', class_='quest-rating-populi__team-count_number').text. \
            replace(' команд', '').replace(' команды', '').replace(' команда', '')
    except AttributeError:
        quest_details_dict['teams_ammount'] = ''
    try:
        review_section = soup.find('section', class_='container reviews-intro')
        spans = review_section.find_all('span')
        quest_details_dict['avg_mark'] = spans[3].text
        quest_details_dict['ammount_of_votes'] = spans[4].text
    except AttributeError:
        quest_details_dict['avg_mark'] = ''
        quest_details_dict['ammount_of_votes'] = ''
    return quest_details_dict


def get_goal_quests() -> list:
    """Get goal links without the domain name
    :return: list with quest links"""
    path = 'goal_quests.txt'
    with open(path, 'r') as f:
        quests = [link.replace('https://mir-kvestov.ru', '').replace('\n', '') for link in f.readlines()]
    logging.info(f'The goal links {len(quests)} is successfully gotten')
    return quests


def merge_people_rating_page_quests_and_goal_quests(goal_quests_in: list, quests_people_rating_in: dict):
    """Update quests_people_rating according to goal_quests
    :param goal_quests_in: list of links without domain name
    :param quests_people_rating_in: dict with key links without domain name (quests_people_rating)"""
    logging.info(f'Quest for analyse as a goal: {len(goal_quests_in)}')
    counter = 0
    for key in quests_people_rating_in:
        if key in goal_quests_in:
            counter += 1
            quests_people_rating_in[key]['goal'] = True
        else:
            quests_people_rating_in[key]['goal'] = False
    logging.info(f'Goal quests found at people rating page: {counter}')
    if len(goal_quests_in) == counter:
        logging.info(f'All links are found in people rating page! Congratulations!!!')


def parse_quest_cycle(links_in) -> dict:
    """
    :param links_in: full links of goal quests
    :return quest_dict: it is the dict with keys are href and values are nested dicts with keys
    (people_rating, teams_ammount, avg_mark, ammount_of_votes, *ammount_of_trusted_votes)"""
    quests_pages = {}
    for link in links_in:
        href = link.replace('https://mir-kvestov.ru/', '')
        time.sleep(max(random.random()*3, 2))
        session = start_session(proxy_use=False)
        try:
            all_quests_html_response = session.get(link)
            quests_pages[href] = parse_quest_page(all_quests_html_response.content)
            logging.info(f'quest page: {href} was successfully parsed!')
        except Exception as err:
            logging.error(f'Some exception happened during handling: {href}')
            logging.error(err, exc_info=False)
            quests_pages[href] = {}
    return quests_pages


def compare_main_and_people_rating(quests_people_rating_in, main_page_quests_dict_in):
    """Update quests_people_rating_in dict by the position of the quest from the main page"""
    for key in quests_people_rating_in.keys():
        try:
            quests_people_rating_in[key]['main_page_position'] = main_page_quests_dict_in[key]['quest_position']
        except KeyError:
            quests_people_rating_in[key]['main_page_position'] = 'not at the first page'
    logging.info('The main page and people rating page dicts are successfully merged')


def compare_people_rating_with_single_quests_dict(quests_people_rating_in, quests_pages_in):
    """Update quests_people_rating_in dict by the average mark and the number of votes"""
    for key in quests_people_rating_in:
        try:
            quests_people_rating_in[key]['avg_mark'] = quests_pages_in[key]['avg_mark']
        except KeyError:
            quests_people_rating_in[key]['avg_mark'] = ''
        try:
            quests_people_rating_in[key]['ammount_of_votes'] = quests_pages_in[key]['ammount_of_votes']
        except KeyError:
            quests_people_rating_in[key]['ammount_of_votes'] = ''
    logging.info('The single quests dict and people rating page dicts are successfully merged')


def parsing_process() -> list:
    """Perform parsing and prepare list with dictionaries with details concerning quests"""
    # Get goal quests from the file
    goal_quests = get_goal_quests()
    # Get all quests in peoples rating page
    quests_people_rating = parse_people_rating(get_people_rating(start_session(proxy_use=False)))
    # Merge the goal links and dict has prepared from page with people rating quests
    merge_people_rating_page_quests_and_goal_quests(goal_quests, quests_people_rating)
    # Get list of the links form parsed
    full_links = ['/'.join([base_url, quests_people_rating[key]['quest_link']])
                  for key in quests_people_rating.keys() if quests_people_rating[key]['goal']]
    [logging.info(link) for link in full_links]
    # Get quest pages necessary content
    quests_pages = parse_quest_cycle(full_links)
    # Get main page and parse it for the quests details
    main_page_quests_dict = parse_main_page(get_main_html(start_session(proxy_use=False)))
    # Include in people rating dict the position of quest from the first page
    compare_main_and_people_rating(quests_people_rating, main_page_quests_dict)
    # Include in people rating dict the avg mark and number of votes
    compare_people_rating_with_single_quests_dict(quests_people_rating, quests_pages)
    list_of_goal_quest_details = [quests_people_rating[key] for key in quests_people_rating.keys()
                                  if quests_people_rating[key]['goal']]
    return list_of_goal_quest_details


if __name__ == '__main__':
    parsing_process()
