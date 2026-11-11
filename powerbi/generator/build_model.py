"""Genererar den semantiska modellen som TMDL.

    python powerbi/generator/build_model.py powerbi/BI-jobbmarknaden.SemanticModel

Tabeller, kolumner, relationer och DAX-mått definieras här i Python och
skrivs som TMDL-filer, som Power BI Desktop läser direkt (PBIP-format).
Filerna checkas in, så att varje ändring i modellen syns i git.
"""
import sys, uuid
from pathlib import Path

ROOT = Path(sys.argv[1])  # .../powerbi/BI-jobbmarknaden.SemanticModel
D = ROOT / "definition"
(D / "tables").mkdir(parents=True, exist_ok=True)
T = "\t"

def q(name):  # TMDL-citering
    return f"'{name}'" if any(c in name for c in " -.()=:'åäöÅÄÖ/") or name[0].isdigit() else name

# (källkolumn, visningsnamn, typ, dold, format, sortera_efter, summarize)
TABLES = {
    "Datum": ("dim_date", [
        ("date", "Datum", "dateTime", False, "yyyy-mm-dd", None, None),
        ("year", "År", "int64", False, "0", None, "none"),
        ("quarter", "Kvartal", "int64", False, "0", None, "none"),
        ("year_quarter", "År-kvartal", "string", False, None, "year_quarter_sort", None),
        ("year_quarter_sort", "year_quarter_sort", "int64", True, "0", None, "none"),
        ("month", "Månad", "int64", False, "0", None, "none"),
        ("month_start", "Månadsstart", "dateTime", False, "yyyy-mm", None, None),
        ("year_month", "År-månad", "string", False, None, "month_start", None),
        ("weekday_number", "Veckodag nr", "int64", True, "0", None, "none"),
        ("iso_week", "Vecka", "int64", False, "0", None, "none"),
        ("is_weekend", "Helg", "boolean", False, None, None, None),
    ]),
    "Term": ("dim_term", [
        ("term_id", "term_id", "string", True, None, None, None),
        ("term", "Term", "string", False, None, None, None),
        ("category", "Kategori", "string", False, None, "category_sort", None),
        ("category_sort", "category_sort", "int64", True, "0", None, "none"),
        ("is_core_bi", "BI-kärnterm", "boolean", False, None, None, None),
        ("vendor", "Leverantör", "string", False, None, None, None),
        ("launched_year", "Lanseringsår", "int64", False, "0", None, "none"),
        ("note", "Not", "string", False, None, None, None),
    ]),
    "Yrkesgrupp": ("dim_occupation_group", [
        ("ssyk4_key", "ssyk4_key", "string", True, None, None, None),
        ("ssyk4", "SSYK", "string", False, None, None, None),
        ("ssyk4_label", "Yrkesgrupp", "string", False, None, None, None),
        ("ssyk3", "SSYK 3", "string", True, None, None, None),
        ("ssyk1", "SSYK 1", "string", True, None, None, None),
        ("ssyk1_label", "Yrkesområde", "string", False, None, None, None),
    ]),
    "Yrke": ("dim_occupation", [
        ("occupation_key", "occupation_key", "string", True, None, None, None),
        ("occupation_label", "Yrke", "string", False, None, None, None),
        ("ssyk4", "SSYK (yrke)", "string", True, None, None, None),
        ("data_role_family", "Datayrkesfamilj", "string", False, None, None, None),
    ]),
    "Län": ("dim_region", [
        ("region_key", "region_key", "string", True, None, None, None),
        ("region_name", "Län", "string", False, None, None, None),
        ("region_group", "Region", "string", False, None, None, None),
        ("is_vastra_gotaland", "Västra Götaland", "boolean", False, None, None, None),
    ]),
    "Kommun": ("dim_municipality", [
        ("municipality_key", "municipality_key", "string", True, None, None, None),
        ("municipality_name", "Kommun", "string", False, None, None, None),
        ("region_key", "region_key", "string", True, None, None, None),
        ("is_gothenburg_region", "Göteborgsregionen", "boolean", False, None, None, None),
    ]),
    "Arbetsgivare": ("dim_employer", [
        ("employer_key", "Organisationsnummer", "string", False, None, None, None),
        ("employer_name", "Arbetsgivare", "string", False, None, None, None),
        ("employer_type", "Sektor", "string", False, None, None, None),
    ]),
    "Dataannons": ("fact_job_ad", [
        ("ad_id", "ad_id", "string", True, None, None, None),
        ("published_date", "published_date", "dateTime", True, None, None, None),
        ("municipality_key", "municipality_key", "string", True, None, None, None),
        ("ssyk4_key", "ssyk4_key", "string", True, None, None, None),
        ("occupation_key", "occupation_key", "string", True, None, None, None),
        ("employer_key", "employer_key", "string", True, None, None, None),
        ("employer_type", "Arbetsgivartyp", "string", False, None, None, None),
        ("number_of_vacancies", "Antal tjänster", "int64", True, "0", None, "sum"),
        ("remote_work", "Distans", "boolean", False, None, None, None),
        ("experience_required", "Kräver erfarenhet", "boolean", False, None, None, None),
        ("employment_type", "Anställningsform", "string", False, None, None, None),
        ("working_hours", "Arbetstid", "string", False, None, None, None),
        ("scope_min", "scope_min", "int64", True, "0", None, "none"),
        ("scope_max", "scope_max", "int64", True, "0", None, "none"),
        ("n_terms", "Antal termer", "int64", True, "0", None, "none"),
        ("mentions_core_bi", "Nämner BI-kärnterm", "boolean", False, None, None, None),
        ("mentions_power_bi", "Nämner Power BI", "boolean", False, None, None, None),
        ("is_data_occupation", "Datayrke enligt arbetsgivaren", "boolean", False, None, None, None),
        ("data_role_family", "data_role_family", "string", True, None, None, None),
        ("location_source", "Ortskälla", "string", False, None, None, None),
        ("occupation_source", "Yrkeskälla", "string", False, None, None, None),
    ]),
    "Annons-term": ("bridge_ad_term", [
        ("ad_id", "ad_id", "string", True, None, None, None),
        ("term_id", "term_id", "string", True, None, None, None),
        ("in_headline", "I rubriken", "boolean", False, None, None, None),
    ]),
    "Annonsvolym": ("fact_ad_volume", [
        ("month_start", "month_start", "dateTime", True, None, None, None),
        ("municipality_key", "municipality_key", "string", True, None, None, None),
        ("ssyk4_key", "ssyk4_key", "string", True, None, None, None),
        ("employer_type", "Arbetsgivartyp (alla)", "string", False, None, None, None),
        ("n_ads", "n_ads", "int64", True, "0", None, "sum"),
        ("n_vacancies", "n_vacancies", "int64", True, "0", None, "sum"),
        ("n_data_ads", "n_data_ads", "int64", True, "0", None, "sum"),
        ("n_core_bi_ads", "n_core_bi_ads", "int64", True, "0", None, "sum"),
        ("n_power_bi_ads", "n_power_bi_ads", "int64", True, "0", None, "sum"),
        ("n_remote_ads", "n_remote_ads", "int64", True, "0", None, "sum"),
    ]),
    "Källjämförelse": ("fact_term_source", [
        ("term_id", "term_id", "string", True, None, None, None),
        ("year", "År (jämförelse)", "int64", False, "0", None, "none"),
        ("n_both", "n_both", "int64", True, "0", None, "sum"),
        ("n_dictionary_only", "n_dictionary_only", "int64", True, "0", None, "sum"),
        ("n_enrichment_only", "n_enrichment_only", "int64", True, "0", None, "sum"),
    ]),
    "Anställda (SCB)": ("fact_employment", [
        ("year", "year", "int64", True, "0", None, "none"),
        ("region_key", "region_key", "string", True, None, None, None),
        ("ssyk4_key", "ssyk4_key", "string", True, None, None, None),
        ("employed", "employed", "int64", True, "0", None, "sum"),
        ("method", "Metod", "string", False, None, None, None),
        ("source_table", "SCB-tabell", "string", False, None, None, None),
    ]),
}

MEASURES = [
    # (namn, dax, format, mapp, beskrivning)
    ("Annonser", "SUM('Annonsvolym'[n_ads])", "#,0", "1 Volym",
     "Alla unika annonser i Platsbanken (nämnaren för andelar)."),
    ("Dataannonser", "COUNTROWS('Dataannons')", "#,0", "1 Volym",
     "Annonser som nämner en BI-kärnterm eller där arbetsgivaren valt ett datayrke."),
    ("Andel dataannonser", "DIVIDE([Dataannonser], [Annonser])", "0.00%", "1 Volym",
     "Dataannonser som andel av alla annonser."),
    ("Annonser som nämner Power BI", "SUM('Annonsvolym'[n_power_bi_ads])", "#,0", "1 Volym", None),
    ("Power BI per 1 000 annonser", "DIVIDE([Annonser som nämner Power BI], [Annonser]) * 1000", "0.0", "1 Volym",
     "Antal annonser som nämner Power BI per 1 000 annonser totalt."),
    ("Båda källorna", "SUM('Källjämförelse'[n_both])", "#,0", "8 Källjämförelse",
     "Annonser där både ordlistan och JobTechs berikning hittar termen."),
    ("Bara ordlistan", "SUM('Källjämförelse'[n_dictionary_only])", "#,0", "8 Källjämförelse",
     "Annonser där bara ordlistan hittar termen."),
    ("Bara JobTechs berikning", "SUM('Källjämförelse'[n_enrichment_only])", "#,0", "8 Källjämförelse",
     "Annonser där bara JobTechs automatiska tolkning hittar termen."),
    ("Överensstämmelse",
     "DIVIDE([Båda källorna], [Båda källorna] + [Bara ordlistan] + [Bara JobTechs berikning])", "0%", "8 Källjämförelse",
     "Andel av alla träffar där källorna är överens."),
    ("Annonser med term",
     "DISTINCTCOUNT('Annons-term'[ad_id])", "#,0", "2 Termer",
     "Unika dataannonser som nämner minst en av de valda termerna. Filter på datum, ort och yrke når bryggan via Dataannons (en-till-många), utan dubbelriktad filtrering."),
    ("Andel som nämner term",
     "DIVIDE([Annonser med term], [Dataannonser])", "0.0%", "2 Termer",
     "Andel av dataannonserna som nämner termen."),
    ("Andel som nämner term, fg år",
     "CALCULATE([Andel som nämner term], SAMEPERIODLASTYEAR('Datum'[Datum]))", "0.0%", "2 Termer", None),
    ("Förändring, procentenheter",
     "VAR nu = [Andel som nämner term]\nVAR fg = [Andel som nämner term, fg år]\nRETURN IF(NOT ISBLANK(nu) && NOT ISBLANK(fg), (nu - fg) * 100)",
     "+0.0;-0.0;0.0", "2 Termer", "Förändring i andel mot samma period året innan, i procentenheter."),
    ("Rang term",
     "IF(\n    ISINSCOPE('Term'[Term]),\n    RANKX(ALLSELECTED('Term'[Term]), [Annonser med term], , DESC, DENSE)\n)",
     "0", "2 Termer", None),
    ("Samförekomst",
     "VAR annonserA = VALUES('Annons-term'[ad_id])\nVAR termerB = VALUES('Term B'[term_id_b])\nVAR annonserB =\n    CALCULATETABLE(\n        VALUES('Annons-term'[ad_id]),\n        REMOVEFILTERS('Term'),\n        TREATAS(termerB, 'Term'[term_id])\n    )\nVAR sammaTerm = SELECTEDVALUE('Term'[term_id]) = SELECTEDVALUE('Term B'[term_id_b])\nRETURN\n    IF(NOT sammaTerm, DIVIDE(COUNTROWS(INTERSECT(annonserA, annonserB)), COUNTROWS(annonserA)))",
     "0%", "2 Termer",
     "Andel av annonserna med term A (Term) som också nämner term B (Term B, frikopplad kopia)."),
    ("Dataannonser fg år",
     "CALCULATE([Dataannonser], SAMEPERIODLASTYEAR('Datum'[Datum]))", "#,0", "3 Tid", None),
    ("Dataannonser, förändring",
     "DIVIDE([Dataannonser] - [Dataannonser fg år], [Dataannonser fg år])", "+0%;-0%;0%", "3 Tid", None),
    ("Dataannonser, rullande 12 mån",
     "CALCULATE(\n    [Dataannonser],\n    DATESINPERIOD('Datum'[Datum], MAX('Datum'[Datum]), -12, MONTH)\n)", "#,0", "3 Tid", None),
    ("Anställda",
     "VAR ar = VALUES('Datum'[År])\nRETURN CALCULATE(SUM('Anställda (SCB)'[employed]), TREATAS(ar, 'Anställda (SCB)'[year]))",
     "#,0", "4 SCB",
     "Anställda enligt SCB:s yrkesregister för valda år, län och yrkesgrupper. SCB saknar år efter 2024."),
    ("Dataannonser per 1 000 anställda",
     "VAR perAr =\n    ADDCOLUMNS(VALUES('Datum'[År]), \"@annonser\", [Dataannonser], \"@anstallda\", [Anställda])\nVAR medScb = FILTER(perAr, NOT ISBLANK([@anstallda]))\nRETURN DIVIDE(SUMX(medScb, [@annonser]), SUMX(medScb, [@anstallda])) * 1000",
     "0.00", "4 SCB",
     "Räknas bara för år där SCB har siffror, så att 2025–2026 inte ger en för hög kvot."),
    ("Annonser per 1 000 anställda",
     "VAR perAr =\n    ADDCOLUMNS(VALUES('Datum'[År]), \"@annonser\", [Annonser], \"@anstallda\", [Anställda])\nVAR medScb = FILTER(perAr, NOT ISBLANK([@anstallda]))\nRETURN DIVIDE(SUMX(medScb, [@annonser]), SUMX(medScb, [@anstallda])) * 1000",
     "0.0", "4 SCB", None),
    ("Andel distans", "DIVIDE(CALCULATE([Dataannonser], 'Dataannons'[Distans] = TRUE()), [Dataannonser])",
     "0.0%", "5 Villkor", "Andel dataannonser som anger distansarbete."),
    ("Andel distans, alla annonser", "DIVIDE(SUM('Annonsvolym'[n_remote_ads]), [Annonser])", "0.0%", "5 Villkor", None),
    ("Andel kräver erfarenhet",
     "DIVIDE(CALCULATE([Dataannonser], 'Dataannons'[Kräver erfarenhet] = TRUE()), [Dataannonser])",
     "0.0%", "5 Villkor", None),
    ("Andel offentlig sektor",
     "DIVIDE(CALCULATE([Dataannonser], 'Dataannons'[Arbetsgivartyp] = \"offentlig sektor\"),\n       CALCULATE([Dataannonser], 'Dataannons'[Arbetsgivartyp] IN {\"offentlig sektor\", \"privat sektor\"}))",
     "0.0%", "5 Villkor", "Bland dataannonser med känd sektor (organisationsnummer finns från 2021)."),
    ("Andel utan datayrke",
     "DIVIDE(CALCULATE([Dataannonser], 'Dataannons'[Datayrke enligt arbetsgivaren] = FALSE()), [Dataannonser])",
     "0.0%", "6 Vad är ett BI-jobb",
     "Dataannonser där arbetsgivaren valt ett yrke som inte är ett datayrke, till exempel controller."),
    ("Andel utan ort", "DIVIDE(CALCULATE([Annonser], 'Kommun'[Kommun] = \"Län saknas, kommun saknas\"), [Annonser])",
     "0.0%", "7 Datakvalitet", None),
    ("Senaste annonsdatum", "MAX('Dataannons'[published_date])", "yyyy-mm-dd", "7 Datakvalitet", None),
]

RELATIONSHIPS = [
    ("Dataannons", "published_date", "Datum", "Datum"),
    ("Annonsvolym", "month_start", "Datum", "Datum"),
    ("Dataannons", "municipality_key", "Kommun", "municipality_key"),
    ("Annonsvolym", "municipality_key", "Kommun", "municipality_key"),
    ("Kommun", "region_key", "Län", "region_key"),
    ("Anställda (SCB)", "region_key", "Län", "region_key"),
    ("Dataannons", "ssyk4_key", "Yrkesgrupp", "ssyk4_key"),
    ("Annonsvolym", "ssyk4_key", "Yrkesgrupp", "ssyk4_key"),
    ("Anställda (SCB)", "ssyk4_key", "Yrkesgrupp", "ssyk4_key"),
    ("Dataannons", "occupation_key", "Yrke", "occupation_key"),
    ("Dataannons", "employer_key", "Arbetsgivare", "Organisationsnummer"),
    ("Annons-term", "ad_id", "Dataannons", "ad_id"),
    ("Annons-term", "term_id", "Term", "term_id"),
    ("Källjämförelse", "term_id", "Term", "term_id"),
]

def col_display(table, src):
    for c in TABLES[table][1]:
        if c[0] == src or c[1] == src:
            return c[1]
    raise KeyError((table, src))

def indent(text, n):
    return "\n".join((T * n + line) if line else line for line in text.split("\n"))

def write_table(name, src, cols):
    out = [f"table {q(name)}", f"{T}lineageTag: {uuid.uuid5(uuid.NAMESPACE_URL, 'bi-jobb/' + name)}"]
    if name == "Datum":
        out.append(f"{T}dataCategory: Time")
    out.append("")
    for (s, disp, typ, hidden, fmt, sort_by, summ) in cols:
        out.append(f"{T}column {q(disp)}")
        out.append(f"{T}{T}dataType: {typ}")
        if hidden:
            out.append(f"{T}{T}isHidden")
        if name == "Datum" and s == "date":
            out.append(f"{T}{T}isKey")
        if fmt:
            out.append(f"{T}{T}formatString: {fmt}")
        out.append(f"{T}{T}summarizeBy: {summ or 'none'}")
        out.append(f"{T}{T}sourceColumn: {s}")
        if sort_by:
            out.append(f"{T}{T}sortByColumn: {q(col_display(name, sort_by))}")
        out.append(f"{T}{T}lineageTag: {uuid.uuid5(uuid.NAMESPACE_URL, f'bi-jobb/{name}/{s}')}")
        out.append("")
    m = (f'let\n    Källa = Parquet.Document(File.Contents(DataFolder & "\\{src}.parquet"))\nin\n    Källa')
    out.append(f"{T}partition {q(name)} = m")
    out.append(f"{T}{T}mode: import")
    out.append(f"{T}{T}source =")
    out.append(indent(m, 4))
    out.append("")
    (D / "tables" / f"{name}.tmdl").write_text("\n".join(out), encoding="utf-8")

for name, (src, cols) in TABLES.items():
    write_table(name, src, cols)

# Frikopplad kopia av Term för samförekomst
tb = [
    "table 'Term B'",
    f"{T}lineageTag: {uuid.uuid5(uuid.NAMESPACE_URL, 'bi-jobb/TermB')}",
    "",
]
for col, typ in [("term_id_b", "string"), ("Term B", "string"), ("Kategori B", "string")]:
    tb += [f"{T}column {q(col)}", f"{T}{T}dataType: {typ}", f"{T}{T}isNameInferred",
           f"{T}{T}sourceColumn: [{col}]"]
    if col == "term_id_b":
        tb.append(f"{T}{T}isHidden")
    tb += [f"{T}{T}summarizeBy: none", f"{T}{T}lineageTag: {uuid.uuid5(uuid.NAMESPACE_URL, 'bi-jobb/TermB/' + col)}", ""]
tb += [f"{T}partition 'Term B' = calculated", f"{T}{T}mode: import", f"{T}{T}source =",
       indent("SELECTCOLUMNS(\n    'Term',\n    \"term_id_b\", 'Term'[term_id],\n    \"Term B\", 'Term'[Term],\n    \"Kategori B\", 'Term'[Kategori]\n)", 4), ""]
(D / "tables" / "Term B.tmdl").write_text("\n".join(tb), encoding="utf-8")

# Måtttabell
mt = ["table Mått", f"{T}lineageTag: {uuid.uuid5(uuid.NAMESPACE_URL, 'bi-jobb/Matt')}", ""]
for (name, dax, fmt, folder, desc) in MEASURES:
    if desc:
        mt.append(f"{T}/// {desc}")
    if "\n" in dax:
        mt.append(f"{T}measure {q(name)} =")
        mt.append(indent(dax, 3))
    else:
        mt.append(f"{T}measure {q(name)} = {dax}")
    mt.append(f"{T}{T}formatString: {fmt}")
    mt.append(f"{T}{T}displayFolder: {folder}")
    mt.append(f"{T}{T}lineageTag: {uuid.uuid5(uuid.NAMESPACE_URL, 'bi-jobb/m/' + name)}")
    mt.append("")
mt += [f"{T}column Platshållare", f"{T}{T}dataType: string", f"{T}{T}isHidden", f"{T}{T}summarizeBy: none",
       f"{T}{T}sourceColumn: Platshållare", f"{T}{T}lineageTag: {uuid.uuid5(uuid.NAMESPACE_URL, 'bi-jobb/m/col')}", "",
       f"{T}partition Mått = m", f"{T}{T}mode: import", f"{T}{T}source =",
       indent("let\n    Källa = #table(type table [Platshållare = text], {})\nin\n    Källa", 4), ""]
(D / "tables" / "Mått.tmdl").write_text("\n".join(mt), encoding="utf-8")

rel = []
for (ft, fc, tt, tc) in RELATIONSHIPS:
    rid = uuid.uuid5(uuid.NAMESPACE_URL, f"bi-jobb/rel/{ft}/{fc}")
    rel += [f"relationship {rid}",
            f"{T}fromColumn: {q(ft)}.{q(col_display(ft, fc))}",
            f"{T}toColumn: {q(tt)}.{q(col_display(tt, tc))}", ""]
(D / "relationships.tmdl").write_text("\n".join(rel), encoding="utf-8")

(D / "expressions.tmdl").write_text(
    "/// Mappen med gold-tabellerna som Parquet. Ändra till repots powerbi/data om du inte kör pipelinen själv.\n"
    'expression DataFolder = "C:\\data\\bi-jobbmarknaden\\gold" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]\n'
    f"{T}lineageTag: {uuid.uuid5(uuid.NAMESPACE_URL, 'bi-jobb/DataFolder')}\n", encoding="utf-8")

(D / "database.tmdl").write_text("database\n\tcompatibilityLevel: 1601\n", encoding="utf-8")
order = ["Mått"] + list(TABLES) + ["Term B"]
(D / "model.tmdl").write_text(
    "model Model\n\tculture: sv-SE\n\tdefaultPowerBIDataSourceVersion: powerBI_V3\n\tdiscourageImplicitMeasures\n\tsourceQueryCulture: sv-SE\n\n"
    + "\n".join(f"ref table {q(t)}" for t in order) + "\n", encoding="utf-8")
(ROOT / "definition.pbism").write_text(
    '{\n  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/definitionProperties/1.0.0/schema.json",\n  "version": "4.2",\n  "settings": {}\n}\n',
    encoding="utf-8")
print("ok", len(MEASURES), "mått")
