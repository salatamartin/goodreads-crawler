## Goodreads fantasy crawler
This is a small project for fetching all fantasy books on Goodreads for easier sorting/filtering. It exists because Goodreads doesn't allow you to sort/filter the books directly. Goodreads API is also garbage.

### How to run:
- Create a .credentials file in the project's root directory containing your credentials to Goodreads
    - It should be in format `[username/email]:[password]`, encoded as base64
- Run build-docker.ps1
- Run run-docker.ps1
    - New directory `results` will be created. In it, `books.json` should appear with the results of the crawler

### Technical details
- Crawler has a list of Goodreads shelves and lists
- For each book in the list, it tries to find `name`, `author`, `avg_rating`, `rating_count`, `published` and `from_url` for reference.
    - If some of the information is missing (like year of publishing in some of the lists), the crawler tries to find the missing information on the specific book's page
- For each list, the crawler checks the existence of "next page" of the list. If it exists, it will be crawled too.
