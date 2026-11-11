"""Små byggstenar för PBIR-rapportfiler (Power BI enhanced report format)."""
import json, hashlib
from pathlib import Path

S = "https://developer.microsoft.com/json-schemas/fabric/item/report"
SCHEMA_VISUAL = f"{S}/definition/visualContainer/2.4.0/schema.json"
SCHEMA_PAGE = f"{S}/definition/page/2.0.0/schema.json"


def hid(*parts):
    return hashlib.sha1("/".join(parts).encode()).hexdigest()[:20]


def lit(v):
    if isinstance(v, bool):
        return {"expr": {"Literal": {"Value": "true" if v else "false"}}}
    if isinstance(v, (int, float)):
        return {"expr": {"Literal": {"Value": f"{v}D"}}}
    return {"expr": {"Literal": {"Value": "'" + str(v).replace("'", "''") + "'"}}}


def color(hex_):
    return {"solid": {"color": lit(hex_)}}


def col(entity, prop):
    return {"Column": {"Expression": {"SourceRef": {"Entity": entity}}, "Property": prop}}


def meas(entity, prop):
    return {"Measure": {"Expression": {"SourceRef": {"Entity": entity}}, "Property": prop}}


def proj(field, display=None):
    kind = "Column" if "Column" in field else "Measure"
    e = field[kind]["Expression"]["SourceRef"]["Entity"]
    p = field[kind]["Property"]
    out = {"field": field, "queryRef": f"{e}.{p}", "nativeQueryRef": p}
    if display:
        out["displayName"] = display
    return out


def sort_by(field, direction="Descending"):
    return {"sortDefinition": {"sort": [{"field": field, "direction": direction}], "isDefaultSort": False}}


def title(text, size=12):
    return {
        "title": [{"properties": {"show": lit(True), "text": lit(text), "fontSize": lit(size),
                                  "fontColor": color("#1F2A37"), "bold": lit(True)}}],
        "background": [{"properties": {"show": lit(True), "color": color("#FFFFFF"), "transparency": lit(0)}}],
        "border": [{"properties": {"show": lit(True), "color": color("#E5E7EB"), "radius": lit(6)}}],
        "padding": [{"properties": {"top": lit(8), "bottom": lit(8), "left": lit(10), "right": lit(10)}}],
    }


def visual(page, name, vtype, x, y, w, h, roles=None, objects=None, container=None, extra_query=None, z=0):
    v = {"visualType": vtype, "drillFilterOtherVisuals": True}
    if roles:
        qs = {role: {"projections": projs} for role, projs in roles.items()}
        v["query"] = {"queryState": qs}
        if extra_query:
            v["query"].update(extra_query)
    if objects:
        v["objects"] = objects
    if container:
        v["visualContainerObjects"] = container
    return {
        "$schema": SCHEMA_VISUAL,
        "name": hid(page, name),
        "position": {"x": x, "y": y, "z": z, "width": w, "height": h, "tabOrder": z},
        "visual": v,
    }


def textbox(page, name, x, y, w, h, paragraphs, z=0):
    """paragraphs: list of (text, size, bold, color)."""
    paras = []
    for text, size, bold, colr in paragraphs:
        style = {"fontSize": f"{size}pt", "color": colr}
        if bold:
            style["fontWeight"] = "bold"
        paras.append({"textRuns": [{"value": text, "textStyle": style}]})
    return {
        "$schema": SCHEMA_VISUAL,
        "name": hid(page, name),
        "position": {"x": x, "y": y, "z": z, "width": w, "height": h, "tabOrder": z},
        "visual": {
            "visualType": "textbox",
            "objects": {"general": [{"properties": {"paragraphs": paras}}]},
            "visualContainerObjects": {"background": [{"properties": {"show": lit(False)}}]},
            "drillFilterOtherVisuals": True,
        },
    }


def write_report(root: Path, model_dir_name: str, pages: list, theme: dict):
    """pages: list of dict(name, display, visuals=[...], filters=[...])"""
    d = root / "definition"
    if d.exists():
        # OneDrive och Power BI Desktop kan hålla mappar låsta en kort stund
        import os, shutil, stat, time

        def force(func, path, _exc):
            os.chmod(path, stat.S_IWRITE)  # OneDrive kan sätta skrivskydd
            func(path)

        for _ in range(10):
            try:
                shutil.rmtree(d, onexc=force)
            except OSError:
                pass
            if not d.exists():
                break
            time.sleep(1)
        else:
            raise SystemExit(f"Kunde inte ta bort {d}. Stäng Power BI Desktop och försök igen.")
    (d / "pages").mkdir(parents=True)
    (root / "definition.pbir").write_text(json.dumps({
        "$schema": f"{S}/definitionProperties/2.0.0/schema.json",
        "version": "4.0",
        "datasetReference": {"byPath": {"path": f"../{model_dir_name}"}},
    }, indent=2), encoding="utf-8")
    (d / "version.json").write_text(json.dumps({
        "$schema": f"{S}/definition/versionMetadata/1.0.0/schema.json", "version": "2.0.0"}, indent=2), encoding="utf-8")
    res = root / "StaticResources" / "RegisteredResources"
    res.mkdir(parents=True, exist_ok=True)
    (res / "bi-jobbmarknaden-tema.json").write_text(json.dumps(theme, indent=2, ensure_ascii=False), encoding="utf-8")
    (d / "report.json").write_text(json.dumps({
        "$schema": f"{S}/definition/report/3.0.0/schema.json",
        "themeCollection": {"customTheme": {"name": "bi-jobbmarknaden-tema.json",
                                            "reportVersionAtImport": {"visual": "2.4.0", "report": "3.0.0", "page": "2.0.0"},
                                            "type": "RegisteredResources"}},
        "resourcePackages": [{"name": "RegisteredResources", "type": "RegisteredResources",
                              "items": [{"name": "bi-jobbmarknaden-tema.json", "path": "bi-jobbmarknaden-tema.json",
                                         "type": "CustomTheme"}]}],
        "settings": {"useStylableVisualContainerHeader": True, "defaultDrillFilterOtherVisuals": True,
                     "allowChangeFilterTypes": True, "useEnhancedTooltips": True},
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    order = []
    for p in pages:
        pid = hid("page", p["name"])
        order.append(pid)
        pd = d / "pages" / pid
        (pd / "visuals").mkdir(parents=True)
        page = {"$schema": SCHEMA_PAGE, "name": pid, "displayName": p["display"],
                "displayOption": "FitToPage", "height": 720, "width": 1280,
                "objects": {"background": [{"properties": {"color": color("#F5F6F8"), "transparency": lit(0)}}]}}
        if p.get("filters"):
            page["filterConfig"] = {"filters": p["filters"]}
        (pd / "page.json").write_text(json.dumps(page, indent=2, ensure_ascii=False), encoding="utf-8")
        for v in p["visuals"]:
            vd = pd / "visuals" / v["name"]
            vd.mkdir()
            (vd / "visual.json").write_text(json.dumps(v, indent=2, ensure_ascii=False), encoding="utf-8")
    (d / "pages" / "pages.json").write_text(json.dumps({
        "$schema": f"{S}/definition/pagesMetadata/1.0.0/schema.json",
        "pageOrder": order, "activePageName": order[0]}, indent=2), encoding="utf-8")


def _src(alias, entity):
    return {"Name": alias, "Entity": entity, "Type": 0}


def in_filter(name, entity, prop, values, alias="f"):
    """Kategorifilter: entity[prop] IN values."""
    vals = [[lit(v)["expr"]] for v in values]
    return {
        "name": name,
        "field": col(entity, prop),
        "type": "Categorical",
        "filter": {
            "Version": 2,
            "From": [_src(alias, entity)],
            "Where": [{"Condition": {"In": {
                "Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": alias}}, "Property": prop}}],
                "Values": vals}}}],
        },
    }


def topn_filter(name, entity, prop, measure_entity, measure, n):
    return {
        "name": name,
        "field": col(entity, prop),
        "type": "TopN",
        "filter": {
            "Version": 2,
            "From": [
                {"Name": "subquery", "Expression": {"Subquery": {"Query": {
                    "Version": 2,
                    "From": [_src("d", entity), _src("m", measure_entity)],
                    "Select": [{"Column": {"Expression": {"SourceRef": {"Source": "d"}}, "Property": prop}, "Name": "field"}],
                    "OrderBy": [{"Direction": 2, "Expression": {"Measure": {"Expression": {"SourceRef": {"Source": "m"}}, "Property": measure}}}],
                    "Top": n}}}, "Type": 2},
                _src("d", entity),
            ],
            "Where": [{"Condition": {"In": {
                "Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": "d"}}, "Property": prop}}],
                "Table": {"SourceRef": {"Source": "subquery"}}}}}],
        },
    }


def range_filter(name, entity, prop, lo):
    """entity[prop] >= lo (heltal)."""
    return {
        "name": name,
        "field": col(entity, prop),
        "type": "Advanced",
        "filter": {
            "Version": 2,
            "From": [_src("f", entity)],
            "Where": [{"Condition": {"Comparison": {
                "ComparisonKind": 2,
                "Left": {"Column": {"Expression": {"SourceRef": {"Source": "f"}}, "Property": prop}},
                "Right": {"Literal": {"Value": f"{lo}L"}}}}}],
        },
    }


def with_filters(v, filters):
    v["filterConfig"] = {"filters": filters}
    return v
