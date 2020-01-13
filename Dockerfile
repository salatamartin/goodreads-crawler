FROM python:3.8-buster

RUN mkdir /workdir && mkdir /workdir/results
COPY requirements.txt /workdir
WORKDIR /workdir
RUN pip3 install -r requirements.txt

COPY . /workdir
ENTRYPOINT [ "scrapy", "runspider", "src/goodreads_spider.py", "-o", "results/books.json"]