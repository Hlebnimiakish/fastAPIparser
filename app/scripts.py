# pylint: disable=import-error

"""This module contains scripts to parse lamoda goods data"""

import json
import re

import requests
from bs4 import BeautifulSoup
from transliterate import translit

from app.database import CollectionHandler
from app.schema import CategoryModel, GoodModel
from app.settings import settings

URL = 'https://lamoda.by'
session = requests.Session()
lamoda_db_name = settings.lamoda_db_name


class CatalogGood:  # pylint: disable=too-few-public-methods
    """Instanciate a Catalog Good class representing a good from lamoda catalog
    with it's attributes, price, title and brand set"""
    def __init__(self, nuxt_var: str | None):
        """Collects all good parameter from passed in nuxt variable data, and
        put data to CatalogGood instance attributes"""
        self.price = self.brand = self.title = self.attributes = None
        if nuxt_var:
            start = nuxt_var.find('{"product"')
            end = nuxt_var.find('settings:')
            json_data = json.loads(nuxt_var[start:end].rstrip().rstrip(','))
            self.attributes = json_data['product']['attributes']
            self.price = json_data['product']['price']
            self.brand = json_data['product']['brand']['title']
            self.title = json_data['product']['title']

    @classmethod
    def goods_runner(cls, links: list[str], collection_name: str):
        """Takes list of goods links, search for data for each good
        passed, returns lis of CatalogGood instances"""
        for link in links:
            nuxt_var = DataCollectingTools.nuxt_finder(link)
            good = CatalogGood(nuxt_var)
            good_data = GoodModel.good_data_creator(good.title,
                                                    good.brand,
                                                    good.attributes,
                                                    good.price)
            collection = CollectionHandler(lamoda_db_name, collection_name)
            collection.insert_one(good_data)


class DataCollectingTools:
    """Contains collection of methods for lamoda web pages data collecting"""
    @staticmethod
    def soup_maker(link: str) -> BeautifulSoup:
        """Takes in a URL (link) and returns parsed BeautifulSoup instance
        of passed in page URL"""
        page = session.get(link, timeout=300)
        parsed_page = BeautifulSoup(page.content, 'lxml')
        return parsed_page

    @classmethod
    def nuxt_finder(cls, link: str) -> str | None:
        """Search for first javascript __NUXT__ variable, which contains valuable data,
        returns full text of <script> tag containing NUXT variable"""
        parsed_page = cls.soup_maker(link)
        scripts = parsed_page.find_all('script')
        nuxt = None
        for script in scripts:
            if "__NUXT__" not in script.text:
                continue
            nuxt = script.text
            break
        return nuxt

    @classmethod
    def goods_links_getter(cls, link: str, page_num: int | None = None) -> list[str]:
        """Collects all goods links from passed in page link with set page number
        parameter, returns list of all goods links from the page"""
        if page_num:
            link = link + f"?page={page_num}"
        parsed_page = cls.soup_maker(link)
        all_page_goods_links = [URL + good['href'] for good in
                                parsed_page.find_all('a',
                                                     {"class": "x-product-card__link"})]
        return all_page_goods_links

    @classmethod
    def category_subcategories_getter(cls, link: str) -> list[str]:
        """Checks weather category has less than 10 000 positions (as lamoda parses
        only 167 pages with 60 positions on each page) and adds links to all categories
        and subcategories, which has less than 10 000 positions
        (of a given parent category)"""
        parsed_page = cls.soup_maker(link)
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
        for subcategory in too_big_subcategories:
            subcategory_links += cls.category_subcategories_getter(subcategory)
        for category in subtree.find_all('li'):
            subcategory_links.append(URL + category.a['href'])
        return subcategory_links

    @classmethod
    def page_runner(cls, link: str, collection: str):
        """Takes in category link and runs through all category pages collecting
        goods links and passing them to CatalogGood goods runner function"""
        page_num = 1
        remembered_good = None
        for _ in range(167):
            gotten_goods = \
                cls.goods_links_getter(link, page_num)
            if not gotten_goods:
                break
            if gotten_goods and remembered_good and \
                    gotten_goods[-1] == remembered_good:
                break
            CatalogGood.goods_runner(list(gotten_goods),
                                     collection)
            page_num += 1
            remembered_good = gotten_goods[-1]


class HomeCategoriesCollector:
    """Instanciate a HomeCategoriesCollector class with set category map attribute,
    containing actual lamoda home categories and their links"""
    def __init__(self):
        """Creates a current actual category map and assign it to category_map
        class attribute"""
        self.category_map = self.get_categories_map()

    @staticmethod
    def get_category_types() -> dict[str, str]:
        """Finds current actual category types and returns them
        as dict with their names and links"""
        parsed_home = DataCollectingTools.soup_maker(URL)
        type_links = {}
        for tag in parsed_home.body.find_all("a", {"class": "d-header-genders_link"}):
            href = str(tag['href'])
            category_type = tag.string
            category_type_link = URL + href
            type_links[category_type] = category_type_link
        return type_links

    @staticmethod
    def special_categories_links_getter() -> dict[str, dict[str, str | list]]:
        """Collects special category links from homepage, as they can not be gotten
        from standard pages workflow, returns dict with special links and their names"""
        special_links_map = {}
        nuxt_var = DataCollectingTools.nuxt_finder(URL)
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

    def get_categories_map(self) -> dict[str, dict[str, str]]:
        """Finds current actual site categories and their subcategories and returns
        them as dict with their names and links"""
        type_links = self.get_category_types()
        category_map = {}
        for key, value in type_links.items():
            sub_categories = {}
            page = session.get(value, timeout=300)
            parsed_page = BeautifulSoup(page.content, 'lxml')
            search_class = "d-header-topmenu-category__link"
            sub_cats_list = parsed_page.body.find_all("a", {"class": search_class})
            special_categories_map = self.special_categories_links_getter()
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

    def put_categories_to_db(self):
        """Adds collected categories to "categories" lamoda db collection"""
        collection = CollectionHandler(lamoda_db_name, "categories")
        for category_type, subcategories in self.category_map.items():
            category = CategoryModel.category_data_creator(category_type,
                                                           subcategories)
            collection.insert_one(category)


class CategoryDataScraper:
    """Instanciate a CategoryDataScraper class with scraping category link set and class
    link attribute and calls suitable data scraping method"""
    def __init__(self, category_type: str, subcategory: str):
        """Collects actual category map data, gets category link and
        calls suitable data scraper method for requested category"""
        collection = CollectionHandler(lamoda_db_name, "categories")
        category = collection.find_one({"category_type": category_type})
        self.collection_name = self.collection_name_generator(category_type,
                                                              subcategory)
        if category:
            self.link = category["subcategories"][subcategory]
            category_methods_map: dict = {"Блог": self.blog_data_scraper,
                                          "Бренды": self.brands_data_scraper,
                                          "Новинки": self.new_goods_data_scraper}
            if subcategory in category_methods_map:
                category_methods_map[subcategory]()
            else:
                self.standard_data_scraper()

    @staticmethod
    def links_runner(links: list, collection: str):
        """Runs through links passed in the links list and calls page_runner
        method from DataCollectingTools class to get data from all available
        pages"""
        for link in links:
            DataCollectingTools.page_runner(link, collection)

    @staticmethod
    def collection_name_generator(category_type: str, category_name: str):
        """Generates translit name from given category type and category name
        for mongo db collection"""
        category_collection = f'{category_type.lower()}_{category_name.lower()}'
        collection_name = translit(category_collection, "ru", reversed=True)
        return collection_name

    @staticmethod
    def categories_collector(link: str) -> list:
        """Collects all available categories from a given page link, returns
        list of available category links"""
        parsed_page = DataCollectingTools.soup_maker(link)
        categories = parsed_page.find_all('a', {'class': "x-link x-link__label"})
        return categories

    def categories_runner(self, categories: list):
        """Runs through passed in list of category links collects all subcategory link
        lists (via category_subcategories_getter from DataCollectingTools class method)
        and calls a link_runner method for each subcategory links list"""
        for category in categories:
            category_link = URL + category['href']
            links = DataCollectingTools.category_subcategories_getter(category_link)
            self.links_runner(links, self.collection_name)

    def standard_data_scraper(self):
        """Collects all subcategory link lists (via category_subcategories_getter
        from DataCollectingTools class method) and calls a link_runner method for
        each subcategory links list"""
        links = DataCollectingTools.category_subcategories_getter(self.link)
        self.links_runner(links, self.collection_name)

    def blog_data_scraper(self):
        """Prints out a statement"""
        return {"Blog": "Nothing to parse here"}

    def categories_data_scraper(self, link: str):
        """Gets categories by running categories_collector method on a given link and
        calls a categories_runner method to collect data from gotten categories list"""
        categories = self.categories_collector(link)
        self.categories_runner(categories)

    def new_goods_data_scraper(self):
        """Calls categories_data_scraper for a class link attribute"""
        self.categories_data_scraper(self.link)

    def brands_data_scraper(self):
        """Calls categories_data_scraper for each of links inside
        brand links list"""
        for inside_link in self.link:
            self.categories_data_scraper(inside_link)


class ThePageParser:  # pylint: disable=too-few-public-methods
    """Class contains method for goods from passed page link parsing, puts data to
    last_parsed_page collection"""
    collection_name = "last_parsed_page"
    collection = CollectionHandler(lamoda_db_name, collection_name)

    @classmethod
    def parse_passed_page(cls, link):
        """Deletes all class collection (last_parsed_page) documents, parses goods from
        passed page link and puts parsed data to class collection"""
        cls.collection.delete_many({})
        goods_links = DataCollectingTools.goods_links_getter(link)
        if not goods_links:
            cls.collection.insert_one({"parsed_page_link": link,
                                       "status": "Nothing to parse here"})
        else:
            CatalogGood.goods_runner(goods_links, cls.collection_name)
            cls.collection.insert_one({"parsed_page_link": link})
