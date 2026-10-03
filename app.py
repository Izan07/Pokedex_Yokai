import json
import math
import os
import re
import secrets
import unicodedata
from collections import Counter
from pathlib import Path

from flask import Flask, abort, flash, redirect, render_template, request, send_from_directory, session, url_for


BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "yokais.json"
IMAGE_DIR = BASE_DIR / "static" / "images" / "yokais"

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY") or os.urandom(32)

TYPE_CLASSES = {
    "Normal": "normal",
    "Fuego": "fire",
    "Agua": "water",
    "Eléctrico": "electric",
    "Planta": "grass",
    "Hielo": "ice",
    "Lucha": "fighting",
    "Veneno": "poison",
    "Tierra": "ground",
    "Volador": "flying",
    "Psíquico": "psychic",
    "Bicho": "bug",
    "Roca": "rock",
    "Fantasma": "ghost",
    "Dragón": "dragon",
    "Siniestro": "dark",
    "Acero": "steel",
    "Hada": "fairy",
}
TYPE_COLORS = {
    "Normal": "#e6e3d8",
    "Fuego": "#ffd8bd",
    "Agua": "#d4e8ff",
    "Eléctrico": "#ffef9c",
    "Planta": "#d6f0c4",
    "Hielo": "#d9f4f7",
    "Lucha": "#f3c6c2",
    "Veneno": "#e7c7ef",
    "Tierra": "#ead8ad",
    "Volador": "#dcd9ff",
    "Psíquico": "#ffd2df",
    "Bicho": "#e1edaa",
    "Roca": "#ded0a0",
    "Fantasma": "#d9d0ea",
    "Dragón": "#d8ccff",
    "Siniestro": "#d4cdc8",
    "Acero": "#dfe3ec",
    "Hada": "#ffddec",
}
with (BASE_DIR / "data" / "type_effectiveness.json").open("r", encoding="utf-8") as source:
    TYPE_EFFECTIVENESS = json.load(source)

RARITIES = {
    "Clásicos": {"class": "clasicos", "icon": "❖"},
    "Merican": {"class": "merican", "icon": "✦"},
    "Leyenda Merican": {"class": "leyenda-merican", "icon": "★"},
    "Legendarios": {"class": "legendarios", "icon": "♛"},
    "Mítico": {"class": "mitico", "icon": "✧"},
    "Leyenda Mística": {"class": "leyenda-mistica", "icon": "✺"},
}
STAT_FIELDS = (
    ("PS", "ps"),
    ("Ataque", "ataque"),
    ("Defensa", "defensa"),
    ("Ataque Especial", "ataque-especial"),
    ("Defensa Especial", "defensa-especial"),
    ("Velocidad", "velocidad"),
)


def slug_base(name):
    normalized = unicodedata.normalize("NFKD", name.casefold())
    ascii_name = "".join(char for char in normalized if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", "-", ascii_name).strip("-") or "yokai"


def load_raw_yokais():
    with DATA_FILE.open("r", encoding="utf-8") as source:
        data = json.load(source)
    yokais = data.get("yokais")
    if not isinstance(yokais, list):
        raise ValueError("El JSON debe contener una lista 'yokais'.")
    return yokais


def unique_slug(name, used_slugs):
    base = slug_base(name)
    slug = base
    suffix = 2
    while slug in used_slugs:
        slug = f"{base}-{suffix}"
        suffix += 1
    used_slugs.add(slug)
    return slug


def display_types(yokai):
    result = []
    for label in (yokai.get("tipo1", ""), yokai.get("tipo2", "")):
        label = label.strip()
        if label and label not in [item["name"] for item in result]:
            result.append({"name": label, "css_class": TYPE_CLASSES.get(label, "normal")})
    return result


def calculate_type_effectiveness(defending_types):
    result = {"weak": [], "resists": [], "immune": []}
    for attack_type in TYPE_CLASSES:
        matchup = TYPE_EFFECTIVENESS[attack_type]
        multiplier = 1.0
        for defending_type in defending_types:
            if defending_type in matchup["x0"]:
                multiplier = 0.0
                break
            if defending_type in matchup["x2"]:
                multiplier *= 2
            elif defending_type in matchup["x0_5"]:
                multiplier *= 0.5

        entry = {
            "name": attack_type,
            "css_class": TYPE_CLASSES[attack_type],
            "multiplier": f"x{multiplier:g}",
        }
        if multiplier == 0:
            result["immune"].append(entry)
        elif multiplier > 1:
            result["weak"].append(entry)
        elif 0 < multiplier < 1:
            result["resists"].append(entry)
    return result


def get_yokais():
    used_slugs = set()
    yokais = []
    for raw in load_raw_yokais():
        name = str(raw.get("nombre", "")).strip()
        slug = unique_slug(name, used_slugs)
        yokai = dict(raw)
        yokai_types = display_types(raw)
        raw_rarity = raw.get("rareza")
        rarity = raw_rarity if isinstance(raw_rarity, str) and raw_rarity in RARITIES else None
        characteristics = normalize_characteristics(raw.get("caracteristicas"))
        yokai.update(
            slug=slug,
            name=name,
            types=yokai_types,
            type_effectiveness=calculate_type_effectiveness(
                [type_item["name"] for type_item in yokai_types]
            ),
            rareza=rarity,
            rarity_class=RARITIES.get(rarity, {}).get("class"),
            rarity_icon=RARITIES.get(rarity, {}).get("icon"),
            caracteristicas=characteristics,
            stat_rows=[
                {
                    "name": label,
                    "class": css_class,
                    "value": characteristics[label],
                    "width": characteristics[label] * 100 / 255,
                }
                for label, css_class in STAT_FIELDS
            ],
            image_url=url_for("yokai_image", slug=slug),
        )
        yokais.append(yokai)
    return yokais


def save_raw_yokais(yokais):
    temporary_file = DATA_FILE.with_suffix(".tmp")
    with temporary_file.open("w", encoding="utf-8", newline="\n") as destination:
        json.dump({"yokais": yokais}, destination, ensure_ascii=False, indent=4)
        destination.write("\n")
    temporary_file.replace(DATA_FILE)


def normalize_search(value):
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def normalize_characteristics(values):
    values = values if isinstance(values, dict) else {}
    result = {}
    for label, _ in STAT_FIELDS:
        value = values.get(label, 0)
        if isinstance(value, bool):
            value = 0
        elif isinstance(value, int):
            pass
        elif isinstance(value, str) and re.fullmatch(r"\d+", value.strip()):
            value = int(value.strip())
        else:
            value = 0
        result[label] = value if 0 <= value <= 255 else 0
    return result


def find_yokai(slug, yokais=None):
    for position, yokai in enumerate(yokais if yokais is not None else get_yokais()):
        if yokai["slug"] == slug:
            return position, yokai
    return None, None


def form_yokai(existing=None):
    name = request.form.get("name", "").strip()
    type1 = request.form.get("type1", "").strip()
    type2 = request.form.get("type2", "").strip()
    yokai = dict(existing or {})
    yokai.update(nombre=name, tipo1=type1, tipo2=type2)
    rareza = request.form.get("rareza", "").strip()
    if rareza in RARITIES:
        yokai["rareza"] = rareza
    else:
        yokai.pop("rareza", None)
    yokai["caracteristicas"] = normalize_characteristics(
        {label: request.form.get(f"stat_{css_class}", "0") for label, css_class in STAT_FIELDS}
    )
    if not existing:
        yokai["ruta_img"] = ""
    return yokai


def make_pie_slices(type_counts):
    total = sum(type_counts.values())
    if not total:
        return []

    slices = []
    start_angle = -90.0
    for name, count in sorted(type_counts.items(), key=lambda entry: (-entry[1], entry[0])):
        end_angle = start_angle + count * 360 / total
        start_radians = start_angle * 3.141592653589793 / 180
        end_radians = end_angle * 3.141592653589793 / 180
        x1 = 160 + 148 * math.cos(start_radians)
        y1 = 160 + 148 * math.sin(start_radians)
        x2 = 160 + 148 * math.cos(end_radians)
        y2 = 160 + 148 * math.sin(end_radians)
        large_arc = 1 if end_angle - start_angle > 180 else 0
        percentage = count * 100 / total
        slices.append(
            {
                "name": name,
                "count": count,
                "percentage": f"{percentage:.2f}",
                "color": TYPE_COLORS.get(name, "#d9e1ec"),
                "css_class": TYPE_CLASSES.get(name, "normal"),
                "path": f"M 160 160 L {x1:.3f} {y1:.3f} A 148 148 0 {large_arc} 1 {x2:.3f} {y2:.3f} Z",
            }
        )
        start_angle = end_angle
    return slices


@app.route("/public/images/yokais/<slug>.jpg")
def yokai_image(slug):
    expected_file = IMAGE_DIR / f"{slug}.jpg"
    if expected_file.is_file():
        return send_from_directory(IMAGE_DIR, expected_file.name)

    _, yokai = find_yokai(slug)
    if yokai is None:
        abort(404)

    source_path = str(yokai.get("ruta_img", ""))
    source_name = re.split(r"[\\/]", source_path)[-1]
    if source_name and Path(source_name).name == source_name and (IMAGE_DIR / source_name).is_file():
        return send_from_directory(IMAGE_DIR, source_name)
    source_stem = Path(source_name).stem
    source_stem = re.sub(r"^\s*\d+[ ._-]+", "", source_stem)
    lookup_names = [source_stem, yokai["name"]]

    image_files = sorted(
        (path for path in IMAGE_DIR.iterdir() if path.is_file() and path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}),
        key=lambda path: path.name.casefold(),
    ) if IMAGE_DIR.is_dir() else []
    images_by_slug = {slug_base(path.stem): path for path in image_files}
    for lookup_name in lookup_names:
        matching_file = images_by_slug.get(slug_base(lookup_name))
        if matching_file is not None:
            return send_from_directory(IMAGE_DIR, matching_file.name)
    abort(404)


@app.route("/")
def index():
    yokais = get_yokais()
    search = normalize_search(request.args.get("search", "").strip())
    selected_types = {value for value in request.args.getlist("type") if value}
    type_count = request.args.get("type_count", "").strip()
    rarity_filter = request.args.get("rareza", "").strip()

    if search:
        yokais = [item for item in yokais if search in normalize_search(item["name"])]
    if selected_types:
        yokais = [item for item in yokais if selected_types.intersection(t["name"] for t in item["types"])]
    if type_count in {"1", "2"}:
        yokais = [item for item in yokais if len(item["types"]) == int(type_count)]
    if rarity_filter == "none":
        yokais = [item for item in yokais if not item["rareza"]]
    elif rarity_filter in RARITIES:
        yokais = [item for item in yokais if item["rareza"] == rarity_filter]

    all_types = sorted({type_item["name"] for item in get_yokais() for type_item in item["types"]})
    return render_template(
        "index.html",
        yokai_list=yokais,
        all_types=all_types,
        rarity_labels=list(RARITIES),
        filters=request.args,
        total_yokai=len(load_raw_yokais()),
    )


@app.route("/yokai/<slug>")
def detail(slug):
    _, yokai = find_yokai(slug)
    if yokai is None:
        abort(404)
    return render_template("detail.html", yokai=yokai)


@app.route("/random")
def random_yokai():
    yokais = get_yokais()
    if not yokais:
        abort(404)

    previous_slug = session.get("last_random_yokai")
    candidates = [yokai for yokai in yokais if yokai["slug"] != previous_slug] or yokais
    chosen = secrets.choice(candidates)
    session["last_random_yokai"] = chosen["slug"]
    return redirect(url_for("detail", slug=chosen["slug"]))


@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        yokai = form_yokai()
        if not yokai["nombre"] or not yokai["tipo1"]:
            flash("El nombre y el tipo principal son obligatorios.", "error")
            return render_template("form.html", yokai=yokai, action="Crear", all_types=sorted(TYPE_CLASSES), rarity_labels=list(RARITIES), stat_fields=STAT_FIELDS)
        yokais = load_raw_yokais()
        yokais.append(yokai)
        save_raw_yokais(yokais)
        flash("Yo-kai creado correctamente.", "success")
        return redirect(url_for("detail", slug=get_yokais()[-1]["slug"]))
    return render_template("form.html", yokai=None, action="Crear", all_types=sorted(TYPE_CLASSES), rarity_labels=list(RARITIES), stat_fields=STAT_FIELDS)


@app.route("/edit/<slug>", methods=["GET", "POST"])
def edit(slug):
    enriched_yokais = get_yokais()
    position, yokai = find_yokai(slug, enriched_yokais)
    if yokai is None:
        abort(404)
    if request.method == "POST":
        raw_yokais = load_raw_yokais()
        updated_yokai = form_yokai(raw_yokais[position])
        if not updated_yokai["nombre"] or not updated_yokai["tipo1"]:
            flash("El nombre y el tipo principal son obligatorios.", "error")
            return render_template("form.html", yokai=updated_yokai, action="Editar", all_types=sorted(TYPE_CLASSES), rarity_labels=list(RARITIES), stat_fields=STAT_FIELDS)
        raw_yokais[position] = updated_yokai
        save_raw_yokais(raw_yokais)
        new_slug = get_yokais()[position]["slug"]
        flash("Yo-kai actualizado correctamente.", "success")
        return redirect(url_for("detail", slug=new_slug))
    return render_template("form.html", yokai=yokai, action="Editar", all_types=sorted(TYPE_CLASSES), rarity_labels=list(RARITIES), stat_fields=STAT_FIELDS)


@app.route("/delete/<slug>", methods=["POST"])
def delete(slug):
    yokais = get_yokais()
    position, yokai = find_yokai(slug, yokais)
    if yokai is None:
        abort(404)
    raw_yokais = load_raw_yokais()
    raw_yokais.pop(position)
    save_raw_yokais(raw_yokais)
    flash(f"{yokai['name']} se ha eliminado.", "success")
    return redirect(url_for("index"))


@app.route("/stats")
def stats():
    type_counts = Counter(
        type_item["name"]
        for yokai in get_yokais()
        for type_item in yokai["types"]
    )
    pie_slices = make_pie_slices(type_counts)
    return render_template(
        "stats.html",
        pie_slices=pie_slices,
        total_type_appearances=sum(type_counts.values()),
    )


@app.route("/favoritos")
def favorites():
    return render_template("favorites.html", yokai_list=get_yokais())


@app.route("/juego")
def guess_yokai_game():
    game_yokais = [
        {
            "slug": yokai["slug"],
            "name": yokai["name"],
            "image_url": yokai["image_url"],
            "types": yokai["types"],
        }
        for yokai in get_yokais()
    ]
    return render_template("guess_game.html", yokais=game_yokais)


if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG", "0") == "1", use_reloader=False)
