import argparse
from collections import defaultdict
from datetime import date
from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from pprint import pprint

import pandas as pd
from jinja2 import Environment, FileSystemLoader, select_autoescape


BASE_DIR = Path(__file__).resolve().parent
FOUNDATION_YEAR = 1920


def get_year_word(years):
    if 11 <= years % 100 <= 14:
        return 'лет'
    last_digit = years % 10
    if last_digit == 1:
        return 'год'
    if 2 <= last_digit <= 4:
        return 'года'
    return 'лет'


def load_products(filepath):
    products = pd.read_excel(filepath, keep_default_na=False)
    return products.to_dict(orient='records')


def group_products(products):
    products_by_category = defaultdict(list)
    for product in products:
        products_by_category[product['Категория']].append(product)
    return dict(sorted(products_by_category.items()))


def render_site(products_by_category=None, current_year=None):
    env = Environment(
        loader=FileSystemLoader(BASE_DIR),
        autoescape=select_autoescape(['html', 'xml']),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template('template.html')
    winery_age = (current_year or date.today().year) - FOUNDATION_YEAR
    rendered_page = template.render(
        winery_age=winery_age,
        year_word=get_year_word(winery_age),
        products_by_category=products_by_category or {},
    )
    (BASE_DIR / 'index.html').write_text(rendered_page, encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(
        description='Генератор сайта винодельни из Excel.',
    )
    parser.add_argument('--data', type=Path, default=BASE_DIR / 'wines.xlsx')
    parser.add_argument('--port', type=int, default=8000)
    parser.add_argument('--build-only', action='store_true')
    parser.add_argument('--show-products', action='store_true')
    args = parser.parse_args()

    products_by_category = group_products(load_products(args.data))
    if args.show_products:
        pprint(products_by_category, sort_dicts=False)
    render_site(products_by_category)
    if not args.build_only:
        handler = partial(SimpleHTTPRequestHandler, directory=str(BASE_DIR))
        with HTTPServer(('127.0.0.1', args.port), handler) as server:
            print(f'Сайт запущен: http://127.0.0.1:{args.port}/index.html',
                  flush=True)
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                pass


if __name__ == '__main__':
    main()
