import scrapy
from scrapy.crawler import CrawlerProcess

url_domain = "https://pokemondb.net"

class Scrapper(scrapy.Spider):
    name = "scrapper"
    start_urls = ["https://pokemondb.net/pokedex/all"]

    def __init__(self):
        super().__init__()
        self.ids_visitados = set()  # Para evitar formas alternativas duplicadas

    def parse(self, response):
        linhas = response.css("table#pokedex > tbody > tr")

        for linha in linhas:
            id_pokemon = linha.css("td.cell-num span::text").get()

            # Ignora formas alternativas
            if id_pokemon in self.ids_visitados:
                continue
            self.ids_visitados.add(id_pokemon)

            nome = linha.css("td.cell-name a.ent-name::text").get()
            elementos = linha.css("td.cell-icon a::text").getall()
            href = linha.css("td.cell-name a.ent-name::attr(href)").get()

            if href:
                url = f"{url_domain}{href}"
                yield response.follow(
                    url,
                    callback=self.parse_pokemon,
                    meta={
                        "id": id_pokemon,
                        "nome": nome,
                        "elementos": elementos,
                        "url": url,
                    }
                )
            else:
                # Yield mesmo sem link
                yield {
                    "id": id_pokemon,
                    "nome": nome,
                    "elementos": elementos,
                    "url": None,
                    "altura": None,
                    "peso": None,
                    "efetividades": [],
                    "habilidades": [],
                    "evolucoes": []
                }

    def parse_pokemon(self, response):
        id_pokemon = response.meta["id"]
        nome = response.meta["nome"]
        elementos = response.meta["elementos"]
        url = response.meta["url"]

        altura = None
        peso = None

        for tr in response.css("table.vitals-table tr"):
            th_text = tr.css("th::text").get()
            if th_text == "Height":
                altura = tr.css("td::text").get()
            elif th_text == "Weight":
                peso = tr.css("td::text").get()

        efetividades = []
        for tabela in response.css("table.type-table"):
            tipos = tabela.css("th a::attr(title)").getall()
            valores = tabela.css("tr:nth-child(2) td")
            for tipo, td in zip(tipos, valores):
                valor_texto = td.css("::text").get()
                valor = valor_texto.replace("½", "0.5").replace("¼", "0.25") if valor_texto else "1x"
                efetividades.append({"tipo": tipo, "multiplicador": valor})

        evolucoes = []
        for container in response.css("div.infocard-list-evo"):
            evolucoes.extend(self.parse_evolucoes(container))

        habilidades_acumuladas = []
        habilidades_links = [
            a for tr in response.css("table.vitals-table tr")
            if tr.css("th::text").get() == "Abilities"
            for a in tr.css("td a")
        ]

        if habilidades_links:
            for a in habilidades_links:
                habilidade_nome = a.css("::text").get()
                habilidade_url = f"{url_domain}{a.css('::attr(href)').get()}"
                yield response.follow(
                    habilidade_url,
                    callback=self.parse_habilidade,
                    meta={
                        "pokemon_id": id_pokemon,
                        "nome": nome,
                        "elementos": elementos,
                        "altura": altura,
                        "peso": peso,
                        "url": url,
                        "efetividades": efetividades,
                        "habilidades_acumuladas": list(habilidades_acumuladas),  # cópia
                        "habilidade_nome": habilidade_nome,
                        "evolucoes": evolucoes
                    }
                )
        else:
            yield {
                "id": id_pokemon,
                "nome": nome,
                "elementos": elementos,
                "url": url,
                "altura": altura,
                "peso": peso,
                "efetividades": efetividades,
                "habilidades": [],
                "evolucoes": evolucoes
            }

    def parse_habilidade(self, response):
        dados = response.meta
        habilidades_acumuladas = list(dados["habilidades_acumuladas"])  # cópia

        efeito = response.css("div.grid-col span::text, div.grid-col p::text").getall()
        efeito = " ".join([t.strip() for t in efeito if t.strip()])

        habilidades_acumuladas.append({
            "nome": dados["habilidade_nome"],
            "url": response.url,
            "efeito": efeito
        })

        yield {
            "id": dados["pokemon_id"],
            "nome": dados["nome"],
            "elementos": dados["elementos"],
            "url": dados["url"],
            "altura": dados["altura"],
            "peso": dados["peso"],
            "efetividades": dados["efetividades"],
            "habilidades": habilidades_acumuladas,
            "evolucoes": dados["evolucoes"]
        }

    def parse_evolucoes(self, evo_container):
        evolucoes = []
        cards = evo_container.css("div.infocard, span.infocard-arrow")
        i = 0
        while i < len(cards):
            card = cards[i]
            classes = card.attrib.get("class", "")
            if "infocard" in classes and "infocard-arrow" not in classes:
                id_pokemon = card.css("small::text").re_first(r"#(\d+)")
                nome = card.css("a.ent-name::text").get()
                url = card.css("a.ent-name::attr(href)").get()
                evolucao = {
                    "id": id_pokemon,
                    "nome": nome,
                    "url": f"{url_domain}{url}" if url else None,
                    "level": None,
                    "item": None
                }
                if i + 1 < len(cards) and "infocard-arrow" in cards[i + 1].attrib.get("class", ""):
                    arrow = cards[i + 1]
                    cond_text = arrow.css("small::text").get()
                    if cond_text:
                        cond_text = cond_text.strip("() ")
                        if "Level" in cond_text:
                            evolucao["level"] = cond_text.replace("Level", "").strip()
                        else:
                            evolucao["item"] = cond_text
                    i += 1
                evolucoes.append(evolucao)
            i += 1
        return evolucoes

# Configuração do Scrapy para gerar o JSON final
process = CrawlerProcess(settings={
    "FEEDS": {
        "pokemon.json": {"format": "json", "overwrite": True}
    }
})

process.crawl(Scrapper)
process.start()
