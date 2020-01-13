import scrapy
from scrapy.http import FormRequest
from scrapy.shell import inspect_response
import re      
import calendar
import itertools
import base64

MONTHS = [calendar.month_name[i] for i in range(1,13)]

# Starting pages for the crawler, all of these can contain "next pages" that will also be crawled
BOOK_LISTS = [
    "https://www.goodreads.com/shelf/show/fantasy?page=1",
    "https://www.goodreads.com/list/show/51.The_Best_Urban_Fantasy",
    "https://www.goodreads.com/list/show/50.The_Best_Epic_Fantasy_fiction_",
    "https://www.goodreads.com/list/show/88.Best_Fantasy_Books_of_the_21st_Century",
    "https://www.goodreads.com/list/show/114178.Popular_Highly_Rated_Fantasy",
    "https://www.goodreads.com/list/show/115751.Best_Fantasy_of_the_20th_Century",
    "https://www.goodreads.com/list/show/2365.Pre_Tolkien_Fantasy",
    "https://www.goodreads.com/list/show/318.Fantasy_Classics",
    "https://www.goodreads.com/list/show/38633.Best_Fantasy_of_the_2010s",
    "https://www.goodreads.com/list/show/38609.Best_Fantasy_of_the_2000s",
    "https://www.goodreads.com/list/show/1118.Best_Fantasy_of_the_90s",
    "https://www.goodreads.com/list/show/1117.Best_Fantasy_of_the_80s",
    "https://www.goodreads.com/list/show/1116.Best_Fantasy_of_the_70s",
    "https://www.goodreads.com/list/show/35857.The_Most_Popular_Fantasy_on_Goodreads",
    "https://www.goodreads.com/list/show/46916.Popular_Fantasy_on_Goodreads_with_between_50000_and_99999_ratings",
    "https://www.goodreads.com/list/show/74893.Popular_Fantasy_on_Goodreads_with_between_25000_and_49999_ratings",
    "https://www.goodreads.com/list/show/76860.Popular_Fantasy_on_Goodreads_with_between_10000_and_24999_ratings",
    "https://www.goodreads.com/list/show/79318.Popular_Fantasy_on_Goodreads_with_between_100_and_999_ratings",
    "https://www.goodreads.com/list/show/80066.Popular_Fantasy_on_Goodreads_with_between_1000_and_9999_ratings",
    "https://www.goodreads.com/list/show/76987.Best_Fantasy_on_Goodreads_with_less_than_100_ratings",
    "https://www.goodreads.com/list/show/115805.Best_Forgotten_Fantasy_of_the_20th_Century",
    "https://www.goodreads.com/list/show/75425",
    "https://www.goodreads.com/list/show/75483",
    "https://www.goodreads.com/list/show/79807",
    "https://www.goodreads.com/list/show/79774",
    "https://www.goodreads.com/list/show/96981",
    "https://www.goodreads.com/list/show/84815",
    "https://www.goodreads.com/list/show/69612",
    "https://www.goodreads.com/list/show/32318",
    "https://www.goodreads.com/list/show/71851",
    # "https://www.goodreads.com/book/show/8694389-deathless"
    # "https://www.goodreads.com/book/show/8480952-the-river-of-shadows"
]

def get_credentials(path):
    '''
    Reads a credential file and parses the credentials.
    Credentials should be in format <username>:<password>, encoded in base64.

    Returns (username, password)
    '''
    with open(path, 'r') as f:
        credentials_encoded = f.read()
    credentials = base64.b64decode(bytes(credentials_encoded, 'utf-8')).decode('utf-8')
    username = credentials.split(':')[0]
    password = credentials.split(':')[1:-1]
    return (username, password)

class GoodreadsSpider(scrapy.Spider):
    name = 'goodreads_spider'
    start_urls = ['https://www.goodreads.com/user/sign_in']

    def parse(self, response):
        token = response.xpath('//*[@name="authenticity_token"]/@value').extract_first()
        username, password = get_credentials('.credentials')
        return FormRequest.from_response(response, 
            formdata={
                'authenticity_token' : token, 
                'user[email]': username, 
                'user[password]': password
            }, 
            callback=self.scrape_after_login)

    def scrape_after_login(self, response):
        return (scrapy.Request(url, callback=self.scrape_book_list) for url in BOOK_LISTS)

    def scrape_book_list(self, response):
        BOOK_SET_SELECTORS = [
            # This one serves for shelves (e.g. /shelf/show/fantasy), but elementList class is in multiple places, so we also filter based on the parent
            '//div[contains(@class, "elementList") and not(parent::div/@id="myBooksResultsContents") and not(parent::div/@class="bigBoxContent containerWithHeaderContent")]', 
            # This is more straightforward and is used in book lists (e.g. /list/show/84815)
            '//tr[contains(@itemtype, "http://schema.org/Book")]']
        books = itertools.chain([response.xpath(selector) for selector in BOOK_SET_SELECTORS])

        for book in books:
            # Here we have to try multiple selectors for some of the attributes, as shelves and lists have different formats
            NAME_SELECTORS = ['.bookTitle::text', '.bookTitle span::text']
            AUTHOR_SELECTORS = ['.authorName span::text']
            INFO_SELECTORS = ['.greyText.smallText::text', '.minirating::text']

            avg_rating, rating_count, published_year = self.parse_info(self.find_first(book, INFO_SELECTORS))
            result =  {
                'name': self.find_first(book, NAME_SELECTORS),
                'author': self.find_first(book, AUTHOR_SELECTORS),
                'avg_rating': avg_rating,
                'rating_count': rating_count,
                'published': published_year,
                'from_url': response.url
            }
            
            # Sometimes lists don't have the publish years, so we crawl inside the details page and try to fetch it from there
            if not published_year:
                yield scrapy.Request(
                    url=response.urljoin(book.css('.bookTitle::attr(href)').extract_first()),
                    callback=self.scrape_details_page,
                    meta={'book': result}
            )
            else:
                yield result

        # Check if we can go to the next page
        NEXT_PAGE_SELECTOR = '.next_page::attr(href)'
        next_page = response.css(NEXT_PAGE_SELECTOR).extract_first()
        if next_page:
            yield scrapy.Request(
                response.urljoin(next_page),
                callback = self.scrape_book_list
            )

    def scrape_details_page(self, response):
        '''
        Parse the details page of a particular book and try to figure out the publish year
        '''

        book_object = response.meta['book']
        # Details part varies quite a lot and is not properly divided, do we just put everyching together and parse as it is
        details_text = ';;'.join(response.xpath('//div[contains(@id, "details")]//div[contains(@class, "row")]').getall())
        try:
            # A lot of possible formats of the defails sections
            YEAR_REGEX = '(th|st|nd|rd|published|Published|%s) *\n? *(\d\d\d\d)' % ('|'.join(MONTHS))
            year = int(re.search(YEAR_REGEX, details_text).group(2))
            book_object['published'] = year
        except Exception as e:
            with open('errors.log', 'a') as fileerr:
                fileerr.write("#################\nCouldn't parse year from '%s' on %s, because %s\n#################\n" %(details_text, response.url, e))
            return book_object
        return book_object

    def find_first(self, document, selectors):
        '''
        Try multiple selectors on a document and return the first successful result
        '''
        for selector in selectors:
            result = document.css(selector).extract_first()
            if result and result.strip():
                return result
        return None

    def find_first_reg(self, regex_list, data):
        '''
        Try multiple regular expressions on a text and return the first successful result
        '''
        for reg in regex_list:
            result = re.search(reg, data)
            if result:
                return result
        return None

    # returns 
    def parse_info(self, info):
        '''
        Parse the book's info text block shown in shelves

        Returns (avg_rating, rating_count, published_year)
        '''
        AVG_RATING_REG = ['avg rating ([\d\.]+)', ' ([\d\.]+) avg rating']
        RATING_COUNT_REG = ['([\d\,]+) ratings']
        PUBLISHED_REG = ['published ([\d]+)']

        try:
            avg_rating = float(self.find_first_reg(AVG_RATING_REG, info).group(1))
        except:
            avg_rating = 0.0

        try:
            rating_count = int(self.find_first_reg(RATING_COUNT_REG, info).group(1).replace(',', ''))
        except:
            rating_count = 0

        try: 
            published_year = int(self.find_first_reg(PUBLISHED_REG, info).group(1))
        except:
            published_year = 0

        return (avg_rating, rating_count, published_year)

