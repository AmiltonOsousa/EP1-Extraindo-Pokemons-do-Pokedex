import scrapy
from scrapy.crawler import CrawlerProcess

url_domain = "https://pokemondb.net"

class Scrapper(scrapy.Spider):
    name = "scrapper"
    start_urls = ["https://pokemondb.net/pokedex/all"]

    def parse(self, response):
        linhas = response.css("table#pokedex > tbody > tr")

        for linha in linhas:
            pokemon_id = linha.css("td:nth-child(1) > span::text").get()
            nome = linha.css("td:nth-child(2) > a::text").get()
            elementos = linha.css("td:nth-child(3) > a::text").getall()
            url = f"{url_domain}{linha.css('td:nth-child(2) a::attr(href)').get()}"

            if url:
                # Passa os dados iniciais via meta para o segundo parse
                yield response.follow(
                    url,
                    callback=self.parse_pokemon,
                    meta={
                        "id": pokemon_id,
                        "nome": nome,
                        "elementos": elementos,
                        "url": url
                    }
                )

    def parse_pokemon(self, response):
        # Recupera os dados passados do parse inicial
        pokemon_id = response.meta["id"]
        nome = response.meta["nome"]
        elementos = response.meta["elementos"]
        url = response.meta["url"]

        # Extrai os detalhes da página individual
        altura = response.css("table.vitals-table tr:contains('Height') td::text").get()
        peso = response.css("table.vitals-table tr:contains('Weight') td::text").get()

        # Yield único com todos os dados
        yield {
            "id": pokemon_id,
            "nome": nome,
            "elementos": elementos,
            "url": url,
            "altura": altura,
            "peso": peso
        }


# Configuração do Crawler
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
