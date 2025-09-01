import scrapy
from scrapy.crawler import CrawlerProcess

url_domain = "https://pokemondb.net"

class Scrapper(scrapy.Spider):
    name = "scrapper"
    start_urls = ["https://pokemondb.net/pokedex/all"]

    def parse(self, response):
        linhas = response.css("table#pokedex > tbody > tr")

        for linha in linhas:
            id = linha.css("td:nth-child(1) > span::text").get()
            nome = linha.css("td:nth-child(2) > a::text").get()
            elementos = linha.css("td:nth-child(3) > a::text").getall()
            url = f"{url_domain}{linha.css('td:nth-child(2) a::attr(href)').get()}"

            yield response.follow(
                url,
                callback=self.parse_pokemon,
                meta={
                    "id": id,
                    "nome": nome,
                    "elementos": elementos,
                    "url": url,
                }
            )

    def parse_pokemon(self, response):
        id = response.meta["id"]
        nome = response.meta["nome"]
        elementos = response.meta["elementos"]
        url = response.meta["url"]

        altura = response.css("table.vitals-table tr:contains('Height') td::text").get()
        peso = response.css("table.vitals-table tr:contains('Weight') td::text").get()

        habilidades_links = response.css("table.vitals-table tr:contains('Abilities') td a")
        habilidades_acumuladas = []

        for a in habilidades_links:
            habilidade_nome = a.css("::text").get()
            habilidade_url = f"{url_domain}{a.css('::attr(href)').get()}"

            yield response.follow(
                habilidade_url,
                callback=self.parse_habilidade,
                meta={
                    "pokemon_id": id,
                    "nome": nome,
                    "elementos": elementos,
                    "altura": altura,
                    "peso": peso,
                    "url": url,
                    "habilidades_acumuladas": habilidades_acumuladas,
                    "habilidade_nome": habilidade_nome
                }
            )

    def parse_habilidade(self, response):
        dados = response.meta
        habilidades_acumuladas = dados["habilidades_acumuladas"]

        efeito = response.xpath("//h2[contains(text(), 'Effect')]/following-sibling::p[1]//text()").getall()
        efeito = " ".join([t.strip() for t in efeito if t.strip()])

        habilidade_obj = {
            "nome": dados["habilidade_nome"],
            "url": response.url,
            "efeito": efeito
        }

        habilidades_acumuladas.append(habilidade_obj)

        yield {
            "id": dados["pokemon_id"],
            "nome": dados["nome"],
            "elementos": dados["elementos"],
            "url": dados["url"],
            "altura": dados["altura"],
            "peso": dados["peso"],
            "habilidades": habilidades_acumuladas
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
