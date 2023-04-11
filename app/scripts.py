"""This module contains scripts to parse lamoda goods data"""

import json
import re

import requests
from bs4 import BeautifulSoup

URL = 'https://lamoda.by'


def nuxt_finder(link: str) -> str | None:
    """Search for first javascript __NUXT__ variable, which contains valuable data,
    returns full text of <script> tag containing NUXT variable"""
    page = requests.get(link, timeout=30)
    parsed_page = BeautifulSoup(page.content, 'lxml')
    scripts = parsed_page.find_all('script')
    nuxt = None
    for script in scripts:
        if "__NUXT__" not in script.text:
            continue
        nuxt = script.text
        break
    return nuxt


def get_category_types() -> dict[str, str]:
    """Finds current actual category types and returns them
    as dict with their names and links"""
    home_page = requests.get(URL, timeout=30)
    parsed_home = BeautifulSoup(home_page.content, 'lxml')
    type_links = {}
    for tag in parsed_home.body.find_all("a", {"class": "d-header-genders_link"}):
        href = str(tag['href'])
        category_type = tag.string
        category_type_link = URL + href
        type_links[category_type] = category_type_link
    return type_links


def special_categories_links_getter() -> dict[str, dict[str, str | list]]:
    """Collects special category links from homepage, as they can not be gotten
    from standard pages workflow, returns dict with special links and their names"""
    special_links_map = {}
    nuxt_var = nuxt_finder(URL)
    if nuxt_var:
        start = nuxt_var.find('{"seo":')
        end = nuxt_var.find('settings:')
        json_data = json.loads(nuxt_var[start:end].rstrip().rstrip(','))
        sections = json_data['seo']['footer']['sections']
        for section in sections:
            title = section['title']
            if title in ["Женщинам", "Мужчинам"]:
                if section['sections']:
                    premium = URL + section['sections'][-1]['links'][0]['link']
                    sport = URL + section['sections'][-1]['links'][1]['link']
                    brands = [URL + brand['link'] for brand in
                              section['sections'][3]['links']]
                    special_links_map[title] = {"Premium": premium,
                                                "Спорт": sport,
                                                "Бренды": brands}
            if title == "Детям":
                brands = [URL + brand["link"] for brand
                          in section['sections'][2]['links']]
                special_links_map[title] = {"Бренды": brands}
    return special_links_map


def get_categories_map() -> dict[str, dict[str, str]]:
    """Finds current actual site categories and their subcategories and returns
    them as dict with their names and links"""
    type_links = get_category_types()
    category_map = {}
    for key, value in type_links.items():
        sub_categories = {}
        page = requests.get(value, timeout=30)
        parsed_page = BeautifulSoup(page.content, 'lxml')
        search_class = "d-header-topmenu-category__link"
        sub_cats_list = parsed_page.body.find_all("a", {"class": search_class})
        special_categories_map = special_categories_links_getter()
        for tag in sub_cats_list:
            category_name = re.sub(r"[\n ]", "", tag.text)
            if key in ["Женщинам", "Мужчинам"] and \
                    category_name not in ['Premium', 'Спорт', 'Бренды'] or \
                    key == "Детям" and category_name != "Бренды":
                href = str(tag['href'])
                category_name_link = URL + href
                sub_categories[category_name] = category_name_link
            else:
                sub_categories[category_name] = \
                    special_categories_map[key][category_name]
        category_map[key] = sub_categories
    return category_map


def goods_links_getter(link: str, page_num: int) -> list[str]:
    """Collects all goods links from passed in page link with set page number
    parameter, returns list of all goods links from the page"""
    link = link + f"?page={page_num}"
    page = requests.get(link, timeout=30)
    parsed_page = BeautifulSoup(page.content, 'lxml')
    all_page_goods_links = [URL + good['href'] for good in
                            parsed_page.find_all('a',
                                                 {"class": "x-product-card__link"})]
    return all_page_goods_links


def category_subcategories_getter(link: str) -> list[str]:
    """Checks weather category has less than 10 000 positions (as lamoda parses
    only 167 pages with 60 positions on each page) and adds links to all categories
    and subcategories, which has less than 10 000 positions
    (of a given parent category)"""
    page = requests.get(link, timeout=30)
    parsed_page = BeautifulSoup(page.content, 'lxml')
    selected_cat = parsed_page.find('div',
                                    {"class":
                                     "x-tree-view-catalog-navigation__category_selected"})
    subcategory_links = []
    too_big_subcategories = []
    subtree = selected_cat.parent.find("ul",
                                       {"class": "x-tree-view-catalog-navigation__subtree"})
    if int(selected_cat.span.text) > 10000:
        for category in subtree.find_all('li'):
            if int(category.span.text) > 10000:
                too_big_subcategories.append(URL + category.a['href'])
            subcategory_links.append(URL + category.a['href'])
    for subcat in too_big_subcategories:
        subcategory_links += category_subcategories_getter(subcat)
    for category in subtree.find_all('li'):
        subcategory_links.append(URL + category.a['href'])
    return subcategory_links


def get_good_data(link: str) -> dict[str, dict | str | float] | None:
    """Collects all good parameter from passed in page link, and returns
    dict with collected good data"""
    nuxt_var = nuxt_finder(link)
    good_data = None
    if nuxt_var:
        start = nuxt_var.find('{"product"')
        end = nuxt_var.find('settings:')
        json_data = json.loads(nuxt_var[start:end].rstrip().rstrip(','))
        attributes = json_data['product']['attributes']
        price = json_data['product']['price']
        brand = json_data['product']['brand']['title']
        title = json_data['product']['title']
        good_data = {"brand": brand, "title": title,
                     "attributes": attributes, "price": price}
    return good_data


def goods_runner(goods_links_list: list):
    """Takes list of goods links, search for data for each good
    passed"""
    for good in goods_links_list:
        good_data = get_good_data(good)
        print(good_data)


def page_runner(link: str) -> list[str]:
    """Takes in category link and runs through all category pages collecting
    goods links, returns collected goods links"""
    page_num = 1
    goods_links = []
    remembered_good = None
    for _ in range(167):
        gotten_goods = goods_links_getter(link, page_num)
        if not gotten_goods:
            break
        if gotten_goods and remembered_good and\
                gotten_goods[-1] == remembered_good:
            break
        goods_runner(gotten_goods)
        page_num += 1
        remembered_good = gotten_goods[-1]
    return goods_links


def parse_goods_data(category_type: str, category_name: str):
    """Takes in name of category type and it's subcategory name to go to,
    for goods data collection, parsing and storing"""
    category_map = get_categories_map()
    link = category_map[category_type][category_name]
    if category_name in ['Одежда', "Обувь", "Аксессуары", "Premium",
                         "Красота", " Sale%", "Спорт", "Мальчикам",
                         "Девочкам", "Малышам", "Игрушки"]:
        links = category_subcategories_getter(link)
        for link in links:
            page_runner(link)
    if category_name == 'Новинки':
        page = requests.get(link, timeout=30)
        parsed_page = BeautifulSoup(page.content, 'lxml')
        categories = parsed_page.find_all('a', {'class': "x-link x-link__label"})
        for category in categories:
            category_link = URL + category['href']
            links = category_subcategories_getter(category_link)
            for link in links:
                page_runner(link)
    if category_name == 'Бренды':
        for inside_link in link:
            page = requests.get(inside_link, timeout=30)
            parsed_page = BeautifulSoup(page.content, 'lxml')
            categories = parsed_page.find_all('a', {'class': "x-link x-link__label"})
            for category in categories:
                category_link = URL + category['href']
                links = category_subcategories_getter(category_link)
                for link in links:
                    page_runner(link)
    if category_name == 'Блог':
        print('Тут я - заглушка!')
