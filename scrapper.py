import scrapy
from scrapy.crawler import CrawlerProcess

class Scrapper(scrapy.Spider):
    name = "scrapper"
    start_urls = ["https://pokemondb.net/pokedex/all"]

    def parse(self, response):
        linhas = response.css("table#pokedex > tbody > tr")

        for linha in linhas:
            yield {
                "id": linha.css("td:nth-child(1) > span::text").get(),
                "nome": linha.css("td:nth-child(2) > a::text").get(),
                "elementos": linha.css("td:nth-child(3) > a::text").getall()
            }

process = CrawlerProcess(settings={
    "FEEDS": {
        "pokemon.json": {
            "format": "json",
            "overwrite": True
        }
    }
})

process.crawl(Scrapper)
process.start()
