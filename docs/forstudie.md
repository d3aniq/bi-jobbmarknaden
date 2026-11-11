# Förstudie: vad efterfrågas i BI-jobben i Västsverige?

Skriven före all kod. Allt nedan är kontrollerat mot källorna 2026-11-11,
bland annat genom ett stickprov på 7 273 annonser från 2024. Där något
inte gick att kontrollera står det uttryckligen.

---

## 1. Frågan

**Hur har efterfrågan på BI- och dataverktyg (Power BI, Fabric,
Databricks, dbt, SQL, Python, Qlik, Tableau med flera) förändrats i
platsannonser i Västra Götaland, jämfört med resten av Sverige, från
2016 till i dag?**

Bakom den finns en svårare fråga: **vad är egentligen ett BI-jobb?** Tre
källor svarar på olika sätt:

| Källa | Hur den avgör vad en annons handlar om |
|---|---|
| Arbetsgivarens yrkesval (SSYK) | det yrke arbetsgivaren valde i formuläret |
| JobTechs berikning | Arbetsförmedlingens automatiska tolkning av annonstexten |
| Egen ordlista | verktygsnamn i annonstexten, med synonymer och undantag |

Olika källor. Ett svar. Precis som i `sweden-power-lakehouse` är det
skillnaderna mellan källorna som är fyndet, inte en felkälla att städa bort.

---

## 2. Källorna

### 2.1 JobTech Historiska annonser (huvudkälla)

| | |
|---|---|
| Ägare | Arbetsförmedlingen, JobTech Dev |
| Innehåll | alla annonser i Platsbanken sedan 2006, över 7 miljoner |
| Licens | **CC0** för annonserna (Apache 2.0 för källkoden), enligt JobTechs dokumentation |
| Åtkomst | ingen nyckel, ingen registrering |
| Format | JSON Lines i zip, en fil per år (per kvartal 2026) |
| Berikade filer | `data.jobtechdev.se/annonser/historiska/berikade/kompletta/`, 2016 till 2026 Q3, cirka 10 GB zippat |
| Oberikade filer | 2006–2015, utan yrkes- och kompetenstolkning |
| Stickprov | `.../berikade/exempel/`, 1 % per år, cirka 10 MB. Används för utveckling och tester. |
| Uppdatering | löpande, ett kvartal i taget |

Fält som används: rubrik, beskrivning (bara för att söka efter ord, se
avsnitt 4), publiceringsdatum, yrke i tre nivåer (yrke, yrkesgrupp med
SSYK-kod, yrkesområde), kommun och län med koder, anställningsform,
omfattning, distansarbete, krav och meriter samt JobTechs berikning
(`keywords.enriched.skill`, `occupation`, `trait`).

### 2.2 JobTech Taxonomy (yrkeshierarki)

`taxonomy.api.jobtechdev.se` ger SSYK-hierarkin, yrkesbenämningar och
kompetensbegrepp med id. Det fungerar utan nyckel (kontrollerat). Licensen
har jag inte kunnat kontrollera, så det görs innan den används. Om den inte
är öppen räcker SSYK-koderna och benämningarna i annonserna.

### 2.3 SCB yrkesregistret (nämnare)

| | |
|---|---|
| Licens | **CC0** för statistikdatabasen. Källa behöver inte anges, men anges ändå. |
| Tabeller | `YREG60` (2014–2018), `YREG60N` (2019–2021), `YREG60BAS` (2020–2024): anställda efter län och yrke (SSYK 2012, 4 siffror), med arbetsplatsens län |
| Åtkomst | PxWeb-API, ingen nyckel |

SCB används för att räkna annonser *per 1 000 anställda* i samma yrke och
län. Utan det jämför man bara regioner av olika storlek.

**Metodbyte:** SCB bytte underlag från RAMS till BAS. Åren 2020 och 2021
finns i båda tabellerna. Skillnaden mellan dem är ett mått på brottet i
serien, och den ska visas och inte jämnas ut. Det är samma sak som
augusti 2024 i förra projektet: två korrekta siffror för samma år.

### 2.4 Avfärdat: JobTechs sök-API för historiska annonser

Det finns ett sök-API (`historical.api.jobtechdev.se`) som borde göra
filerna onödiga. Det ger dock siffror som inte går ihop:

| År | "power bi", riket | "power bi", Västra Götaland | "tableau", riket |
|---|---|---|---|
| 2016 | 39 | 0 | 75 |
| 2018 | **0** | 0 | 144 |
| 2020 | 76 | 8 | 157 |
| 2022 | 127 | 46 | 241 |
| 2024 | 125 | 30 | 165 |
| 2025 | 197 | 33 | 217 |

Noll träffar på Power BI under 2018 är inte trovärdigt. Stickprovet på
1 % av 2024 innehåller 10 annonser som nämner Power BI. Det motsvarar
ungefär 1 000 under året, inte 125. API:et tolkar fritext till begrepp i
sin taxonomi i stället för att söka i texten. Nollorna för Västra
Götaland 2016–2018 tyder dessutom på att ortsuppgiften saknas i de äldre
åren. Det stämmer med att JobTech har publicerat särskilda filer med
rättade kommuner (`municipality_patched`) för 2018 och 2019.

**Slutsats: filerna är källan.** Siffrorna ovan behålls, eftersom de är
ett bra exempel för README:n på varför man inte litar på en sökruta.

---

## 3. Fynd i stickprovet (2024, 1 %, 7 273 annonser)

- **Varje annons har ett nytt `id`.** JobTech skapar det som en
  kontrollsumma. Annonsens ursprungliga id ligger i `original_id`, och
  enligt dokumentationen återkommer det när en annons publiceras igen.
  Dubbletterna måste tas bort på `original_id`.
- **Berikningen fångar inte verktyg.** De vanligaste berikade
  kompetenserna är svenska, engelska, körkort och försäljning. Power BI
  syns knappt. En egen ordlista behövs.
- **Stavningen varierar.** Av tio annonser som nämner Power BI skriver nio
  "powerbi" i ett ord. Ordlistan måste ha synonymer.
- **Västra Götaland är näst störst** med 1 088 annonser, efter Stockholm
  med 2 036.
- **Kontaktfälten är tomma.** `application_contacts`, arbetsgivarens
  e-post och telefon var tomma i hela stickprovet, och beskrivningarna
  innehöll inga e-postadresser eller telefonnummer. JobTech verkar ha
  rensat dem, men det ska testas på hela datan och inte antas.
- **Men det finns personuppgifter ändå**, se avsnitt 4.

---

## 4. Personuppgifter: vad som aldrig lämnar datorn

Annonserna är CC0, men det gör inte varje fält ofarligt att publicera.

- **Enskilda firmor.** En enskild näringsidkares organisationsnummer *är*
  personnumret, och firmanamnet är ofta personens namn. I stickprovet
  innehöll `keywords.extracted.employer` ett namn på en person.
  Arbetsgivare tas därför bara med om organisationsnumret tillhör en
  juridisk person (siffra 3–4 är 20 eller högre). Alla andra blir
  "enskild näringsidkare", utan namn.
- **Annonstexten publiceras aldrig.** Den används bara för att söka efter
  ord i silver. Gold och Power BI-modellen innehåller flaggor per ord,
  inte text.
- **Kontaktfält** tas aldrig med, inte ens i silver.
- **Rådata ligger utanför repot och utanför OneDrive.** Repot ligger i en
  mapp som synkas med OneDrive. 10 GB annonser ska inte dit. Datamappen
  sätts med en miljövariabel, till exempel `C:\data\bi-jobbmarknaden`.

Ett test i gold kontrollerar att inget fält liknar ett personnummer, en
e-postadress eller ett telefonnummer. Om testet hittar något stoppas
bygget.

---

## 5. Ordlistan är den svåra delen

Ordlistan blir en seed i dbt (`term_dictionary.csv`): term, kategori,
reguljärt uttryck och undantag. Den kan granskas och ändras i en pull
request utan att man rör SQL.

Kategorier: visualisering (Power BI, Tableau, Qlik, Looker), plattform
(Fabric, Databricks, Snowflake, Synapse, BigQuery), transformering (dbt,
Data Factory, SSIS, Airflow), språk (SQL, DAX, Python, R, M/Power Query),
moln (Azure, AWS, GCP) och metod (datamodellering, stjärnschema, data
warehouse, lakehouse).

Kända fällor, som var och en ska ha ett test:

| Term | Fälla |
|---|---|
| **dbt** | DBT är också *dialektisk beteendeterapi* och står i annonser för psykologer och behandlare |
| **Fabric** | textil, "fabrik" i engelska annonser |
| **R** | en bokstav. Kräver sammanhang som "R-programmering" eller "R och Python" |
| **Power BI** | "powerbi", "Power-BI", "PBI" |
| **Qlik** | QlikView och Qlik Sense ska räknas som samma verktyg |
| **SQL** | ingår i "SQL Server", "MySQL" och "PostgreSQL". Alla räknas som SQL, men produkten registreras separat. |

---

## 6. Analysfrågor

1. **Hur många annonser per år och kvartal** nämner varje verktyg, i
   Västra Götaland och i övriga Sverige? Absoluta tal och andel av
   BI-annonserna.
2. **Verktygsskiftet.** När passerade Power BI Qlik? Hur snabbt växer
   Fabric och Databricks sedan 2023, och går det att se om Fabric tar
   över från Synapse och Data Factory?
3. **Kombinationer.** Vilka verktyg nämns tillsammans? Power BI med Fabric
   eller med Databricks? SQL med Python? Krävs dbt i samma annonser som
   Databricks?
4. **Vad är ett BI-jobb?** Hur väl stämmer arbetsgivarens yrkesval (SSYK)
   med vad annonsen faktiskt efterfrågar? Hur stor andel av annonserna som
   nämner Power BI ligger utanför de typiska IT-yrkena, till exempel
   controller, ekonom eller verksamhetsutvecklare?
5. **Var?** Göteborg mot övriga kommuner i länet, och Västra Götaland mot
   Stockholm och Skåne. Annonser per 1 000 anställda i yrket enligt SCB.
6. **Villkor.** Andel med distansarbete, tillsvidareanställning och krav
   på erfarenhet för BI-annonser jämfört med alla annonser, över tid.
7. **Konjunktur.** Hur slog nedgången 2023–2024 mot dataannonser jämfört
   med alla annonser?

Platsbanken är inte hela arbetsmarknaden. Många IT-jobb annonseras bara
via LinkedIn eller konsultbolag. README:n ska säga det rakt ut, och
rapporten ska visa trender och andelar hellre än att påstå något om den
totala efterfrågan.

---

## 7. Arkitektur

```
JobTech historiska annonser (zip, 2016–2026 Q3) ─┐
JobTech exempel (1 %, för utveckling och test) ──┼─► bronze: filerna oförändrade + manifest
SCB yrkesregistret (PxWeb JSON) ─────────────────┘   (URL, tid, storlek, SHA-256)
                                                              │
                                     DuckDB läser JSON Lines direkt
                                                              ▼
                     silver (dbt): unika annonser, yrke, ort, ordträffar
                     (annonstexten används här och stannar här)
                                                              │
                                                              ▼
                     gold (dbt): stjärnschema, utan text och utan personuppgifter
                                                              │
                                                     exporteras till Parquet
                                                              ▼
                     Power BI: semantisk modell, DAX, rapport (.pbix i repot)
```

### 7.1 Var pipelinen körs

**Rekommendation: lokalt med DuckDB och dbt-duckdb.**

- Datan är historisk och hämtas en gång. Det finns ingen löpande
  insamling som behöver en server.
- 10 GB JSON klarar DuckDB lokalt utan problem. Det går att läsa direkt
  från JSON Lines utan att packa upp allt först.
- Portfolion har redan ett Databricks-projekt. Det här visar samma
  disciplin i en annan miljö, och vem som helst kan klona repot och köra
  `dbt build` mot stickprovet på några sekunder.
- Power BI läser Parquet direkt, utan gateway eller konto.
- dbt kräver Python 3.12 eller 3.13, och datorn har 3.14. Det löses med en
  separat miljö (uv eller venv), och README:n beskriver hur.

Databricks Free Edition är alternativet. Det ger samma stack som förra
gången men lägger inte till något nytt, och då kan inte vem som helst
köra projektet.

### 7.2 Två körlägen

- **Stickprov** (standard): 1 % per år, cirka 150 MB. Används för
  utveckling, tester och den som bara vill se att det fungerar.
- **Fullt**: alla filer, cirka 10 GB. Ger siffrorna i rapporten.

Samma modeller och samma tester körs i båda lägena, styrt med en
dbt-variabel.

---

## 8. Datamodell (gold)

Stjärnschema. Kornet i faktatabellen är *en unik annons*.

| Tabell | Typ | Innehåll |
|---|---|---|
| `fact_job_ad` | fakta | publiceringsdatum, antal tjänster, omfattning, distans, anställningsform, krav på erfarenhet, BI-flagga, nycklar |
| `bridge_ad_term` | brygga | annons × term, med var termen hittades (rubrik, krav, beskrivning) |
| `dim_term` | dimension | term, kategori, tillverkare, lanseringsår (från seed) |
| `dim_occupation` | dimension | yrke, yrkesgrupp (SSYK 4), SSYK 3, SSYK 2 och yrkesområde |
| `dim_geography` | dimension | kommun, län, Göteborgsregionen ja/nej, landsdel |
| `dim_date` | dimension | datum, månad, kvartal, år |
| `dim_employer_type` | dimension | juridisk person, enskild näringsidkare, offentlig sektor |
| `fact_employment` | fakta | anställda per år, län och SSYK 4 (SCB), med källtabell |

Relationen mellan annons och term är många-till-många. Den löses med
bryggtabellen och en enkelriktad relation från `dim_term`, inte med
dubbelriktad filtrering på hela modellen. Det är ett av de viktigaste
designvalen att förklara i README:n.

DAX-mått (exempel):

- `Annonser`, `BI-annonser`, `Andel BI-annonser %`
- `Annonser med term` (räknar unika annonser via bryggan, inte rader)
- `Andel som nämner term %`, med valfri term som nämnare
- `Förändring mot föregående år` och `Rullande 4 kvartal`
- `Annonser per 1 000 anställda` (mot `fact_employment` på år, län och SSYK)
- `Samförekomst`: andel av annonserna med term A som också nämner term B,
  med två oberoende termväljare (en frikopplad kopia av `dim_term`)
- `Rang` med `RANKX` och topp N med en parameter

Rapporten (förslag, 5 sidor): Översikt · Verktygsskiftet över tid ·
Kombinationer · Vad är ett BI-jobb (yrke mot innehåll) · Var och villkor ·
Datakvalitet.

---

## 9. Kvalitetsgrindar

Samma princip som förut: jobbet ska fallera högt hellre än att leverera
tyst felaktig data. En kontroll som inte kan fallera är ingen kontroll.

| Kontroll | Vad den fångar |
|---|---|
| Rader i bronze mot manifest | att varje fil lästes in helt |
| Unik `original_id` i silver | att återpublicerade annonser inte räknas två gånger |
| Publiceringsdatum inom filens år | annonser i fel fil, eller tidszonsfel vid årsskiftet |
| Kommun och län finns | den kända ortsluckan i de äldre åren |
| Kända SSYK-koder | yrken som annars faller bort i kopplingen till SCB |
| Koppling till SCB över tröskel | att nämnaren finns för de yrken som analyseras |
| **Ingen personuppgift i gold** | personnummer, e-post och telefonnummer, med mönster |
| **Verktyg före lansering** | träffar på Fabric före 2023 eller Databricks före 2015. Det är oftast fel i ordlistan, inte ett verktyg före sin tid. |
| **dbt i vårdyrken** | dbt-träffar i psykolog- och behandlaryrken ska vara noll efter undantagen. Annars räknas terapi som datateknik. |

De tre sista bygger på hur världen ser ut, inte på datatyper, på samma
sätt som "solkraft på natten" förra gången.

---

## 10. Omfattning

### S: snabb (cirka 1 vecka)
- 2020 till 2026 Q3, hela Sverige, Västra Götaland markerat
- ordlista med cirka 15 termer
- ingen SCB-koppling
- rapport: 3 sidor

### M: rekommenderad (cirka 2 veckor)
- 2016 till 2026 Q3, med de rättade ortsfilerna för 2018 och 2019
- ordlista med 30–40 termer, med undantag och ett test per känd fälla
- SCB-nämnare, med metodbytet RAMS–BAS synligt
- samförekomst och frågan om vad ett BI-jobb är
- rapport: 5–6 sidor, med en sida om datakvalitet
- kör även mot stickprovet, så att vem som helst kan reproducera

### L: bredare
- allt i M, plus 2006–2015 (oberikade filer, där bara ordlistan fungerar)
- aktuella annonser via JobTechs JobSearch-API, så att rapporten går fram
  till i dag
- jämförelse mellan JobTechs berikning och ordlistan för alla
  kompetenser, inte bara verktyg

---

## 11. Det här behövs från dig

- **Godkännande av omfattning** (S, M eller L) och av DuckDB lokalt.
- **Inga API-nycklar.** Alla källor är öppna utan registrering.
- **Plats för rådata utanför OneDrive.** Förslag: `C:\data\bi-jobbmarknaden`.
  Det finns 526 GB ledigt.
- **Repots namn.** Förslag: `bi-jobbmarknaden`.

Västtrafik-förstudien ligger kvar i `vasttrafik-punktlighet` om du vill ta
upp den senare.

---

## Källor

- JobTech, historiska annonser (filer): <https://data.jobtechdev.se/annonser/historiska/>
- JobTech, dokumentation och licens: <https://gitlab.com/arbetsformedlingen/job-ads/getting-started-code-examples/historical-ads-info>
- JobTech, sök-API för historiska annonser: <https://historical.api.jobtechdev.se/>
- JobTech Taxonomy API: <https://taxonomy.api.jobtechdev.se/>
- SCB, öppna data och licens: <https://www.scb.se/om-scb/om-scb.se-och-anvandningsvillkor/oppna-data-api/>
- SCB, yrkesregistret (AM0208M): <https://www.statistikdatabasen.scb.se/pxweb/sv/ssd/START__AM__AM0208__AM0208M/>
