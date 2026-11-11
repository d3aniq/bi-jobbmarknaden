"""Genererar rapporten i PBIR-format (Power BI enhanced report format).

    python powerbi/generator/build_report.py powerbi powerbi/generator/fyndtexter.json

Sex sidor, med visualiseringar, filter och färger definierade som kod.
Fyndtexterna ligger i en separat JSON-fil, så att de kan uppdateras när
siffrorna ändras utan att layouten rörs.
"""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from pbir import *  # noqa

ROOT = Path(sys.argv[1])
TEXT = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8")) if len(sys.argv) > 2 else {}
M = "Mått"
INK, INK2, MUTED, LINE = "#0B0B0B", "#52514E", "#8A8984", "#E5E7EB"
BLUE, ORANGE, AQUA, YELLOW, MAGENTA, GREEN, VIOLET, RED = (
    "#2A78D6", "#EB6834", "#1BAF7A", "#EDA100", "#E87BA4", "#008300", "#6250D6", "#E34948")

THEME = {
    "name": "BI-jobbmarknaden",
    "dataColors": [BLUE, ORANGE, AQUA, YELLOW, MAGENTA, GREEN, VIOLET, RED],
    "foreground": INK, "foregroundNeutralSecondary": INK2, "foregroundNeutralTertiary": MUTED,
    "background": "#FFFFFF", "backgroundLight": "#F5F6F8", "backgroundNeutral": "#E5E7EB",
    "tableAccent": BLUE, "good": GREEN, "neutral": YELLOW, "bad": RED,
    "maximum": BLUE, "center": "#F3F4F6", "minimum": "#E8F0FB",
    "textClasses": {
        "callout": {"fontSize": 26, "fontFace": "Segoe UI Semibold", "color": INK},
        "title": {"fontSize": 12, "fontFace": "Segoe UI Semibold", "color": INK},
        "header": {"fontSize": 12, "fontFace": "Segoe UI Semibold", "color": INK},
        "label": {"fontSize": 10, "fontFace": "Segoe UI", "color": INK2},
    },
}

YEAR = col("Datum", "År")
TERM = col("Term", "Term")
REGION = col("Län", "Region")
MAIN_REGIONS = ["Västra Götaland", "Stockholm", "Skåne", "Övriga Sverige"]

# Färgen följer det den visar, inte ordningen: samma term har samma färg i alla diagram.
SERIES_COLORS = {
    ("Län", "Region"): {"Västra Götaland": BLUE, "Stockholm": ORANGE, "Skåne": AQUA, "Övriga Sverige": YELLOW},
    ("Term", "Term"): {
        "Power BI": BLUE, "Qlik": ORANGE, "Tableau": AQUA, "Looker": YELLOW, "SSRS": MAGENTA,
        "Databricks": BLUE, "Microsoft Fabric": ORANGE, "Snowflake": AQUA, "Azure Synapse": YELLOW, "BigQuery": MAGENTA,
        "dbt": BLUE, "Azure Data Factory": ORANGE, "SSIS": AQUA, "Airflow": YELLOW, "Spark": MAGENTA, "Kafka": GREEN,
    },
}


def series_colors(series_field):
    kind = "Column"
    ent = series_field[kind]["Expression"]["SourceRef"]["Entity"]
    prop = series_field[kind]["Property"]
    out = []
    for value, hexc in SERIES_COLORS.get((ent, prop), {}).items():
        out.append({"properties": {"fill": color(hexc)},
                    "selector": {"data": [{"scopeId": {"Comparison": {
                        "ComparisonKind": 0, "Left": series_field,
                        "Right": {"Literal": {"Value": "'" + value + "'"}}}}}]}})
    return out


def t(key, default="(fynd fylls i efter full körning)"):
    return TEXT.get(key, default)


def header(p, heading, sub):
    return textbox(p, "rubrik", 24, 8, 900, 64, [(heading, 18, True, INK), (sub, 10, False, INK2)], z=0)


def notes(p, name, x, y, w, h, heading, body_key, z):
    paras = [(heading, 12, True, INK)]
    for line in t(body_key, "").split("\n"):
        paras.append((line, 10, False, INK2))
    v = textbox(p, name, x, y, w, h, paras, z=z)
    v["visual"]["visualContainerObjects"] = {
        "background": [{"properties": {"show": lit(True), "color": color("#FFFFFF"), "transparency": lit(0)}}],
        "border": [{"properties": {"show": lit(True), "color": color(LINE), "radius": lit(6)}}],
        "padding": [{"properties": {"top": lit(12), "bottom": lit(12), "left": lit(14), "right": lit(14)}}],
    }
    return v


def card(p, name, x, y, w, h, measure, label, z):
    return visual(p, name, "card", x, y, w, h,
                  roles={"Values": [proj(meas(M, measure))]},
                  objects={"labels": [{"properties": {"fontSize": lit(24), "color": color(INK)}}],
                           "categoryLabels": [{"properties": {"show": lit(False)}}]},
                  container=title(label, 10), z=z)


def slicer(p, name, x, y, w, h, field, label, z):
    return visual(p, name, "slicer", x, y, w, h, roles={"Values": [proj(field)]},
                  objects={"data": [{"properties": {"mode": lit("Dropdown")}}],
                           "header": [{"properties": {"show": lit(True), "text": lit(label)}}]},
                  container={"background": [{"properties": {"show": lit(False)}}],
                             "border": [{"properties": {"show": lit(False)}}]}, z=z)


def line(p, name, x, y, w, h, heading, category, values, series=None, filters=None, z=0):
    roles = {"Category": [proj(category)], "Y": [proj(v) for v in values]}
    if series is not None:
        roles["Series"] = [proj(series)]
    v = visual(p, name, "lineChart", x, y, w, h, roles=roles,
               objects={"lineStyles": [{"properties": {"strokeWidth": lit(2), "showMarker": lit(True),
                                                       "markerSize": lit(4)}}],
                        "legend": [{"properties": {"show": lit(True), "position": lit("Top")}}],
                        "categoryAxis": [{"properties": {"axisType": lit("Categorical"), "showAxisTitle": lit(False)}}],
                        "valueAxis": [{"properties": {"showAxisTitle": lit(False), "gridlineColor": color("#EEEEEE")}}]},
               container=title(heading), z=z)
    if series is not None and series_colors(series):
        v["visual"]["objects"]["dataPoint"] = series_colors(series)
    return with_filters(v, filters) if filters else v


def bars(p, name, x, y, w, h, heading, category, value, filters=None, vtype="clusteredBarChart", z=0, labels=True):
    v = visual(p, name, vtype, x, y, w, h,
               roles={"Category": [proj(category)], "Y": [proj(value)]},
               extra_query=sort_by(value),
               objects={"labels": [{"properties": {"show": lit(labels), "color": color(INK2), "fontSize": lit(9)}}],
                        "categoryAxis": [{"properties": {"showAxisTitle": lit(False)}}],
                        "valueAxis": [{"properties": {"show": lit(False), "showAxisTitle": lit(False)}}],
                        "dataPoint": [{"properties": {"fill": color(BLUE)}}]},
               container=title(heading), z=z)
    return with_filters(v, filters) if filters else v


def stacked(p, name, x, y, w, h, heading, category, values, colors, z=0):
    v = visual(p, name, "barChart", x, y, w, h,
               roles={"Category": [proj(category)], "Y": [proj(m) for m in values]},
               extra_query=sort_by(values[0]),
               objects={"legend": [{"properties": {"show": lit(True), "position": lit("Top")}}],
                        "categoryAxis": [{"properties": {"showAxisTitle": lit(False)}}],
                        "valueAxis": [{"properties": {"showAxisTitle": lit(False)}}],
                        "dataPoint": [{"properties": {"fill": color(c)},
                                       "selector": {"metadata": f"{M}.{m['Measure']['Property']}"}}
                                      for m, c in zip(values, colors)]},
               container=title(heading), z=z)
    return v


def matrix(p, name, x, y, w, h, heading, rows, columns, values, filters=None, gradient_measure=None, z=0):
    roles = {"Rows": [proj(rows)], "Values": [proj(values)]}
    if columns is not None:
        roles["Columns"] = [proj(columns)]
    objects = {"columnHeaders": [{"properties": {"fontColor": color(INK), "backColor": color("#FFFFFF")}}],
               "rowHeaders": [{"properties": {"fontColor": color(INK)}}],
               "subTotals": [{"properties": {"rowSubtotals": lit(False), "columnSubtotals": lit(False)}}],
               "values": [{"properties": {"fontColor": color(INK)}}]}
    if gradient_measure:
        m_entity, m_prop = gradient_measure
        objects["values"].append({
            "properties": {"backColor": {"solid": {"color": {"expr": {"FillRule": {
                "Input": meas(m_entity, m_prop),
                "FillRule": {"linearGradient2": {
                    "min": {"color": {"Literal": {"Value": "'#FFFFFF'"}}},
                    "max": {"color": {"Literal": {"Value": "'#5B9BE6'"}}},
                    "nullColoringStrategy": {"strategy": {"Literal": {"Value": "'asZero'"}}}}}}}}}}},
            "selector": {"data": [{"dataViewWildcard": {"matchingOption": 1}}], "metadata": f"{m_entity}.{m_prop}"},
        })
    v = visual(p, name, "pivotTable", x, y, w, h, roles=roles, objects=objects, container=title(heading), z=z)
    return with_filters(v, filters) if filters else v


# ---------------------------------------------------------------- sidor

def p_oversikt():
    p = "oversikt"
    return {"name": p, "display": "Översikt", "visuals": [
        header(p, "Vad efterfrågas i BI-jobben?",
               "Platsbanken 2016 – 2026 K3. Västra Götaland jämfört med resten av Sverige. Källor: JobTech (CC0), SCB (CC0)."),
        card(p, "k1", 24, 84, 296, 92, "Annonser", "Alla annonser", 1),
        card(p, "k2", 336, 84, 296, 92, "Dataannonser", "Dataannonser", 2),
        card(p, "k3", 648, 84, 296, 92, "Andel dataannonser", "Andel dataannonser", 3),
        card(p, "k4", 960, 84, 296, 92, "Power BI per 1 000 annonser", "Power BI per 1 000 annonser", 4),
        line(p, "andel_region", 24, 192, 760, 300, "Andel dataannonser per år och region",
             YEAR, [meas(M, "Andel dataannonser")], series=REGION,
             filters=[in_filter("fRegion", "Län", "Region", MAIN_REGIONS)], z=5),
        bars(p, "topp_vg", 800, 192, 456, 300, "Mest nämnda termer i Västra Götaland, 2025 – 2026 K3",
             TERM, meas(M, "Annonser med term"),
             filters=[in_filter("fVG", "Län", "Västra Götaland", [True]),
                      range_filter("fAr", "Datum", "År", 2025),
                      topn_filter("fTop", "Term", "Term", M, "Annonser med term", 12)], z=6),
        notes(p, "fynd", 24, 508, 1232, 196, "Det viktigaste", "oversikt", 7),
    ]}


def p_skifte():
    p = "skifte"
    def cat_line(name, x, y, w, h, heading, category):
        return line(p, name, x, y, w, h, heading, YEAR, [meas(M, "Andel som nämner term")], series=TERM,
                    filters=[in_filter("fKat", "Term", "Kategori", [category]), range_filter("fAr", "Datum", "År", 2016)])
    v = [
        header(p, "Verktygsskiftet", "Andel av dataannonserna som nämner verktyget, per år."),
        slicer(p, "region", 1016, 12, 240, 56, REGION, "Region", 1),
        cat_line("vis", 24, 84, 616, 304, "Visualisering", "Visualisering"),
        cat_line("plattform", 656, 84, 600, 304, "Plattformar", "Plattform"),
        cat_line("transform", 24, 400, 616, 304, "Transformering", "Transformering"),
        notes(p, "fynd", 656, 400, 600, 304, "Vad som hände", "skifte", 9),
    ]
    for i, x in enumerate(v[2:5], start=2):
        x["position"]["z"] = x["position"]["tabOrder"] = i
    return {"name": p, "display": "Verktygsskiftet", "visuals": v}


COMBO_TERMS = ["Power BI", "Qlik", "Tableau", "Excel", "SQL", "Python", "DAX", "Azure", "Databricks",
               "Microsoft Fabric", "Snowflake", "dbt", "Azure Data Factory", "Data warehouse", "Generativ AI"]


def p_kombinationer():
    p = "kombinationer"
    return {"name": p, "display": "Kombinationer", "visuals": [
        header(p, "Vilka verktyg nämns tillsammans?",
               "Raden är term A, kolumnen term B. Cellen är andelen av annonserna med A som också nämner B."),
        slicer(p, "region", 1016, 12, 240, 56, REGION, "Region", 1),
        matrix(p, "samforekomst", 24, 84, 880, 620, "Samförekomst, 2022 – 2026 K3",
               TERM, col("Term B", "Term B"), meas(M, "Samförekomst"),
               filters=[in_filter("fA", "Term", "Term", COMBO_TERMS),
                        in_filter("fB", "Term B", "Term B", COMBO_TERMS),
                        range_filter("fAr", "Datum", "År", 2022)],
               gradient_measure=(M, "Samförekomst"), z=2),
        notes(p, "fynd", 920, 84, 336, 620, "Så läser du", "kombinationer", 3),
    ]}


def p_bijobb():
    p = "bijobb"
    return {"name": p, "display": "Vad är ett BI-jobb", "visuals": [
        header(p, "Vad är ett BI-jobb?",
               "Arbetsgivarens yrkesval jämfört med vad annonsen faktiskt efterfrågar."),
        card(p, "k1", 24, 84, 296, 92, "Andel utan datayrke", "Dataannonser utan datayrke", 1),
        bars(p, "yrken_pbi", 24, 192, 600, 512, "Yrken i annonser som nämner Power BI, topp 15",
             col("Yrke", "Yrke"), meas(M, "Annonser med term"),
             filters=[in_filter("fT", "Term", "Term", ["Power BI"]),
                      topn_filter("fTop", "Yrke", "Yrke", M, "Annonser med term", 15)], z=2),
        stacked(p, "kallor", 640, 84, 616, 320, "Ordlistan mot JobTechs automatiska tolkning, alla annonser",
                TERM, [meas(M, "Båda källorna"), meas(M, "Bara ordlistan"), meas(M, "Bara JobTechs berikning")],
                [BLUE, AQUA, ORANGE], z=3),
        notes(p, "fynd", 640, 420, 616, 284, "Vad det betyder", "bijobb", 4),
    ]}


def p_var():
    p = "var"
    return {"name": p, "display": "Var och villkor", "visuals": [
        header(p, "Var finns jobben, och på vilka villkor?",
               "Dataannonser per 1 000 anställda i samma yrkesgrupp och län (SCB), samt villkor över tid."),
        bars(p, "per_lan", 24, 84, 600, 304, "Dataannonser per 1 000 anställda, 2022 – 2024",
             col("Län", "Län"), meas(M, "Dataannonser per 1 000 anställda"),
             filters=[range_filter("fAr", "Datum", "År", 2022),
                      in_filter("fReg", "Län", "Region", MAIN_REGIONS)], z=1),
        bars(p, "gbg", 640, 84, 616, 304, "Göteborgsregionen: dataannonser per kommun, 2016 – 2026 K3",
             col("Kommun", "Kommun"), meas(M, "Dataannonser"),
             filters=[in_filter("fGbg", "Kommun", "Göteborgsregionen", [True])], z=2),
        line(p, "distans", 24, 400, 600, 304, "Andel som anger distansarbete",
             YEAR, [meas(M, "Andel distans"), meas(M, "Andel distans, alla annonser")],
             filters=[range_filter("fAr", "Datum", "År", 2016)], z=3),
        notes(p, "fynd", 640, 400, 616, 304, "Vad det betyder", "var", 4),
    ]}


def p_kvalitet():
    p = "kvalitet"
    return {"name": p, "display": "Datakvalitet", "visuals": [
        header(p, "Datakvalitet", "Det här är vad datan klarar av, och var den brister."),
        bars(p, "per_manad", 24, 84, 1232, 280, "Alla annonser per publiceringsmånad",
             col("Datum", "Månadsstart"), meas(M, "Annonser"), vtype="clusteredColumnChart", z=1, labels=False),
        matrix(p, "ortskalla", 24, 380, 600, 324, "Varifrån orten kommer (dataannonser)",
               col("Dataannons", "Ortskälla"), YEAR, meas(M, "Dataannonser"), z=2),
        notes(p, "fynd", 640, 380, 616, 324, "Kända brister", "kvalitet", 3),
    ]}


if __name__ == "__main__":
    pages = [p_oversikt(), p_skifte(), p_kombinationer(), p_bijobb(), p_var(), p_kvalitet()]
    # Kolumndiagrammet per månad ska sorteras i tidsordning, inte efter värde
    pages[5]["visuals"][1]["visual"]["query"].pop("sortDefinition", None)
    write_report(ROOT / "BI-jobbmarknaden.Report", "BI-jobbmarknaden.SemanticModel", pages, THEME)
    (ROOT / "BI-jobbmarknaden.pbip").write_text(
        '{\n  "$schema": "https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json",\n'
        '  "version": "1.0",\n  "artifacts": [\n    {\n      "report": {\n        "path": "BI-jobbmarknaden.Report"\n      }\n    }\n  ],\n'
        '  "settings": {\n    "enableAutoRecovery": true\n  }\n}\n', encoding="utf-8")
    print("ok", len(pages), "sidor")
