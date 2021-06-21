import os
import csv
import time
import requests
import pandas as pd
from inspect import stack
from urllib.parse import urlparse
from requests.exceptions import ConnectionError, MissingSchema

from tqdm import tqdm
from selenium import webdriver
from bs4 import BeautifulSoup, Tag


class bcolors:
    HEADERS = '\033[1m'
    WARNING = '\033[91m'
    OK = '\033[92m'
    OKBLUE = '\033[94m'
    ENDC = '\033[0m'
    UNDERLINE = '\033[4m'
    B = '\033[3m'


class Parser:

    ATTRS = {}
    PAGE = 1
    DUPLICATES = 0
    EXPERIMENTAL = False
    DEFAULT_URL = None

    def __init__(self, skill, file, pages=5, write_to_file=True, drop_duplicate=True, get_report=True, experimental_parsers=False):
        self.URL = self.DEFAULT_URL
        self.FILENAME = file
        self.pages = pages
        self.skill = skill
        self.HEADERS = {
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36'
        }
        self.write_to_file = write_to_file
        self.drop_duplicate = drop_duplicate
        self.get_report = get_report
        self.experimental_parsers = experimental_parsers
        self.show_table = pd.DataFrame(columns=['head', "company", "date", "city", "link"])
        try:
            self.old_lenght_values = len(open(self.FILENAME).readlines())
        except FileNotFoundError:
            with open(self.FILENAME, "a") as file:
                columns = ['head', "company", "date", "city", "link"]
                writer = csv.DictWriter(file, fieldnames=columns)
                writer.writeheader()
            self.old_lenght_values = 0

    def get_data(self, new_address=None):
        def get_description():
            if self.EXPERIMENTAL:
                print(f"{bcolors.WARNING}WARNING: The parser for {urlparse(self.URL).netloc} is slower than normal. "
                      f"Approximate waiting time - 5 minute{bcolors.ENDC}")
            print(f"{bcolors.OK}{str(urlparse(self.URL).netloc)} parsing ...{bcolors.ENDC}")
        # TODO: refactor conditions
        if self.experimental_parsers is False and self.EXPERIMENTAL:
            return None
        if stack()[1][3] == "pipeline":  # If "get_data" called form "pipeline" (first time)
            get_description()
        if new_address:
            return self._get_url(new_address, new_address=True)
        if "{page}" in self.URL:
            for page in range(self.pages):
                self._get_url(self.URL.format_map({"query": self.skill, "page": page + 1}))
                self.PAGE += 1
        else:
            self.pages = 1
            self._get_url(self.URL.format_map({"query": self.skill}))

    def _get_url(self, url: str, new_address=False):
        try:
            r = requests.get(url, headers=self.HEADERS)
        except MissingSchema:
            r = requests.get("https://"+url, headers=self.HEADERS)
        if r.status_code == 200:
            return self._get_html(r.text, new_address)
        raise ConnectionError

    def _get_html(self, html: str, new_address=False):
        soup = BeautifulSoup(html, 'lxml')
        if new_address:
            return soup
        return self._get_table(soup)

    def _get_table(self, soup: BeautifulSoup) -> str:
        table = soup.find_all(**self.ATTRS)
        with tqdm(total=len(table)) as pbar:
            for tag in table:
                pbar.update(1)
                pbar.set_description(" ... Processing page number {}".format(self.PAGE))
                if self.write_to_file:
                    try:
                        self.write_to_csv(self._pars_discription(tag))
                    except AttributeError:
                        pass
                else:
                    self.show_table = self._set_table(self._pars_discription(tag))


            if self.PAGE == self.pages:
                if not self.write_to_file:
                    self._show()
                elif self.get_report:
                    return self.resume()

    def _pars_discription(self, tag: Tag) -> dict:
        head = tag.find('tag', class_="vacancy-serp-item__info").text
        company = tag.find('tag', class_="vacancy-serp-item__meta-info-company").text
        date = tag.find('span', class_="vacancy-serp-item__publication-date vacancy-serp-item__publication-date_short").text
        city = tag.find('span', class_="vacancy-serp-item__meta-info").text
        link = tag.find('a')["href"]
        return {'head': head, "company": company, "date": date, "city": city, "link": link}

    def write_to_csv(self, fields: dict) -> None:
        fields = {k: v.strip() for k, v in fields.items()}
        columns = list(fields.keys())
        if self.drop_duplicate:
            if [True for line in csv.DictReader(open(self.FILENAME)) if line["link"] == fields["link"]] is True:
                self.DUPLICATES += 1
                return None
        with open(self.FILENAME, "a") as file:
            writer = csv.DictWriter(file, fieldnames=columns)
            writer.writerow(fields)

    def _set_table(self, discription: dict):
        # Just set new values
        return self.show_table.append(discription, ignore_index=True)

    def _show(self):
        from http.server import HTTPServer, CGIHTTPRequestHandler
        server_address = ("", 8000)
        httpd = HTTPServer(server_address, CGIHTTPRequestHandler)
        httpd.serve_forever()
        # print(self.show_table.head(len(self.show_table)))  # Show all DataFrame

        self.show_table = pd.DataFrame(columns=self.show_table.columns)  # Clear DataFrame

    def resume(self) -> str:
        new_lenght_values = len(open(self.FILENAME).readlines())
        print("Added {} new values".format(new_lenght_values-self.old_lenght_values))
        print("PATH: {}".format(os.path.abspath(self.FILENAME)))
        answer = lambda b: 'YES' if b else 'NO'
        print(f"{answer(self.write_to_file)} write to file\n{answer(self.drop_duplicate)} drop duplicate")
        print(f"Find {self.DUPLICATES} duplicates")
        return "resume"


class HH(Parser):
    ATTRS = {"name": "div",
             "class": "vacancy-serp-item"}
    DEFAULT_URL = "https://rostov.hh.ru/search/vacancy?L_save_area=true&clusters=true&enable_snippets=true&text={query}&showClusters=true&page={page}"
    def _pars_discription(self, tag: Tag) -> dict:
        head = tag.find('div', class_="vacancy-serp-item__info").text
        company = tag.find('div', class_="vacancy-serp-item__meta-info-company").text
        date = tag.find('span', class_="vacancy-serp-item__publication-date vacancy-serp-item__publication-date_short").text
        city = tag.find('span', class_="vacancy-serp-item__meta-info").text
        link = tag.find('a')["href"]
        return {'head': head, "company": company, "date": date, "city": city, "link": link}


class Trud(Parser):  # experimental
    ATTRS = {"name": "div",
             "class": "item hover"}
    DEFAULT_URL = "https://www.trud.com/jobs/i_{query}/page/{page}"
    EXPERIMENTAL = True
    def _get_url(self, url: str, new_address=False):
        options = webdriver.ChromeOptions()
        options.add_argument('headless')

        browser = webdriver.Chrome(options=options)
        browser.get(url)
        # WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.NAME, "container")))

        time.sleep(3)
        response = browser.page_source
        return self._get_html(response, new_address)

    def _pars_discription(self, tag: Tag) -> dict:
        head = tag.find("div", class_="title").text
        company = tag.find("a", class_="company-link").text
        date = "N/A"
        city = tag.find("span", class_="link-glyph geo-location").text
        link = tag.find("a", class_="item-link")["href"]
        return {'head': head, "company": company, "date": date, "city": city, "link": link}


class Worki(Parser):
    ATTRS = {"name": "div",
             "class": "jobCard_wrapper__2f3oN"}
    DEFAULT_URL = "https://rnd.vkrabota.ru/vacansii/?distanceTo=13&keyWord={query}&salary=1"
    def _pars_discription(self, tag: Tag) -> dict:
        head = tag.find("a").text
        company = tag.find("div", class_="jobCard_companyBlock__1JeHH").text
        city = tag.find("div", class_="jobCard_footer__2BRo-").text
        link = format(urlparse(self.URL).netloc) + tag.find("a")["href"]
        date = "N/A"
        return {'head': head, "company": company, "date": date, "city": city, "link": link}


class Rabota(Parser):
    ATTRS = {"name": "article",
             "class": "vacancy-preview-card vacancy-preview-card_snippet r-serp__item r-serp__item_vacancy"}
    DEFAULT_URL = "https://rostov.rabota.ru/vacancy/?query={query}&sort=relevance"
    def _pars_discription(self, tag: Tag) -> dict:
        def get_date(url: str, kwargs: dict) -> str:

            soup = self.get_data(url)
            result = soup.find(**kwargs).text  # "Вакансия опубликована \d \month \YYYY"
            date = result.split()[2:4]  # ['\d', '\month']
            return self.format_date(date)

        head = tag.find('h3', class_="vacancy-preview-card__title").text
        company = tag.find('span', class_="vacancy-preview-card__company-name").text
        city = tag.find('span', class_="vacancy-preview-location__address-text").text
        link = format(urlparse(self.URL).netloc) + tag.find('h3', class_="vacancy-preview-card__title").find('a')["href"]
        date = get_date(link, {'name': 'span', 'class': "vacancy-system-info__updated-date"})
        return {'head': head, "company": company, "date": date, "city": city, "link": link}

    def format_date(self, raw_date: list) -> str:
        MONTHS = ["янв", "фев", "мар", "апр", "мая", "июн", "июл", "авг", "сен", "окт", "ноя", "дек"]
        changer = lambda l: (l[0], l[1]) if l[0].isdigit() else (l[1], l[0])  # 0 - date; 1 - month
        date, month = changer(raw_date)
        digit_month = [str(i + 1) for i, m in enumerate(MONTHS) if m in month][0]
        return ".".join(map(lambda num: "0" + num if len(num) == 1 else num, (date, digit_month))).strip()


class SuperJob(Parser):
    ATTRS = {"name": "div",
             "class": "f-test-search-result-item"}
    DEFAULT_URL = "https://russia.superjob.ru/vacancy/search/?keywords={query}&page={page}"
    def _pars_discription(self, tag: Tag) -> dict:
        head = tag.find('a').text
        company = tag.find('span', class_="_1h3Zg _3Fsn4 f-test-text-vacancy-item-company-name e5P5i _2hCDz _2ZsgW _2SvHc").text
        multiresult = tag.find('span', class_="_1h3Zg f-test-text-company-item-location e5P5i _2hCDz _2ZsgW").text
        city = multiresult.split("•")[1:][0].split(',')[0]
        date = multiresult.split("•")[:1][0]
        link = format(urlparse(self.URL).netloc) + tag.find('a')["href"]
        return {'head': head, "company": company, "date": date, "city": city, "link": link}


class Gorodrabot(Parser):
    ATTRS = {"name": "div",
             "class": ["result-list__snippet vacancy snippet snippet_clickable",
                       "result-list__snippet vacancy snippet snippet_clickable snippet_advertising"]}
    DEFAULT_URL = "https://russia.gorodrabot.ru/{query}?p={page}"
    def _pars_discription(self, tag: Tag) -> dict:
        head = tag.find("h2", class_="snippet__title").text
        company = tag.find("li", class_="snippet__meta-item snippet__meta-item_company").text
        date = "N/A"
        city = tag.find("li", class_="snippet__meta-item snippet__meta-item_location").text
        link = tag.find("a")["href"]
        return {'head': head, "company": company, "date": date, "city": city, "link": link}


class HabrCareer(Rabota):
    ATTRS = {"name": "div",
             "class": "section-box"}
    DEFAULT_URL = "https://career.habr.com/vacancies?page={page}&q={query}&type=all"
    def _pars_discription(self, tag: Tag) -> dict:
        head = tag.find("div", class_="vacancy-card__title").text
        company = tag.find("div", class_="vacancy-card__company").text
        date = self.format_date(tag.find("div", class_="vacancy-card__date").text.split())
        city = tag.find("div", class_="vacancy-card__meta").text.split("·")[0]
        link = format(urlparse(self.URL).netloc) + tag.find("a")["href"]
        return {'head': head, "company": company, "date": date, "city": city, "link": link}


class Zarplata(Trud, Rabota):
    ATTRS = {"name": "div",
             "class": "ui segment vacancy-item_2MEaq"}
    DEFAULT_URL = "https://russia.zarplata.ru/vacancy?q={query}&limit=100"
    EXPERIMENTAL = True
    def _pars_discription(self, tag: Tag) -> dict:
        head = tag.find("div", class_="header-container_Vsqzm").text
        company = tag.find("div", class_="container_1HMgE").text
        city = tag.find("span", class_="ui text grey").text
        date = self.format_date(tag.find("span", class_="date_1wrLu").text.split())
        link = format(urlparse(self.URL).netloc) + tag.find("a")["href"]
        return {'head': head, "company": company, "date": date, "city": city, "link": link}


# TODO: class Avito


def get_site(attrs: dict) -> None:
    COMPANIES = ["hh.ru", "rabota.ru", "superjob.ru", "career.habr.com", "trud.com",
                 "zarplata.ru", "worki.ru", "vakant.ru", "gorodrabot.ru"]
    site = [n for n in COMPANIES if n in urlparse(attrs).netloc][0]
    if site == "rabota.ru":
        Rabota(**attrs)
    elif site == "hh.ru":
        HH(**attrs)
    elif site == "superjob.ru":
        SuperJob(**attrs)
    elif site == "career.habr.com":
        HabrCareer(**attrs)
    elif ("trud.com" in site) or (site == "www.trud.com"):
        Trud(**attrs)
    elif ("vkrabota.ru" in site) or (site == "vkrabota.ru"):
        Worki(**attrs)
    elif ("gorodrabot.ru" in site) or (site == "russia.gorodrabot.ru"):
        Gorodrabot(**attrs)
    elif ("zarplata.ru" in site) or (site == "russia.zarplata.ru"):
        Zarplata(**attrs)
    else:
        print(f"{bcolors.WARNING}Sorry, something went wrong, try another link or come back later{bcolors.ENDC}")


def pipeline(attrs: dict) -> None:
    SITES = [HH, Trud, Rabota, SuperJob, HabrCareer, Zarplata, Worki, Gorodrabot]
    try:
        old_value = len(open(attrs['file']).readlines())
    except FileNotFoundError:
        old_value = 0
    for site in SITES:
        parser = site(**attrs)
        parser.get_data()
    new_value = len(open('vacancies.csv').readlines())
    print(f"{bcolors.OK}Parsing over! Adding {new_value - old_value} new values!{bcolors.ENDC}")



