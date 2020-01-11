import scrapy
import re      


def get_start_urls():
    base = 'https://www.goodreads.com/shelf/show/fantasy'
    page_property = 'page=%s'
    url_list = []
    for i in range(1,26):
        url_list.append("%s?%s" % (base, page_property % i))
    return url_list


class GoodreadsSpider(scrapy.Spider):
    name = 'goodreads_spider'
    start_urls = get_start_urls()

    AVG_RATING_REG = 'avg rating ([\d\.]+)'
    RATING_COUNT_REG = '([\d\,]+) ratings'
    PUBLISHED_REG = 'published ([\d]+)'

    PAGE_NUMBER_REGEX = 'page=([\d]+)'

    def parse(self, response):
        page_number = re.search(self.PAGE_NUMBER_REGEX, response.url).group(1)
        # print(response.url)
        SET_SELECTOR = '.left'
        for book in response.css(SET_SELECTOR):
            # print(book)
            NAME_SELECTOR = '.bookTitle::text'
            AUTHOR_SELECTOR = '.authorName span::text'
            INFO_SELECTOR = '.greyText.smallText::text'

            avg_rating, rating_count, published_year = self.parse_info(book.css(INFO_SELECTOR).extract_first())
            yield {
                'name': book.css(NAME_SELECTOR).extract_first(),
                'author': book.css(AUTHOR_SELECTOR).extract_first(),
                'avg_rating': avg_rating,
                'rating_count': rating_count,
                'published': published_year,
                'page_number': page_number
            }

        # NEXT_PAGE_SELECTOR = '//a[contains(class, "next_page")]'
        # next_page = response.xpath(NEXT_PAGE_SELECTOR).getall()
        # print(next_page)
        # if next_page:
        #     yield scrapy.Request(
        #         response.urljoin(next_page),
        #         callback = self.parse
        #     )

    # returns(avg_rating, rating_count, published_year)
    def parse_info(self, info):
        try:
            avg_rating = float(re.search(self.AVG_RATING_REG, info).group(1))
            rating_count = int(re.search(self.RATING_COUNT_REG, info).group(1).replace(',', ''))
            published_year = int(re.search(self.PUBLISHED_REG, info).group(1))
            return (avg_rating, rating_count, published_year)
        except Exception as e:
            print("Could not parse info %s, because: %s" % (info, e))
            return (0.0, 0, 0)

