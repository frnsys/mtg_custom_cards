import os
import io
import requests
import lxml.html
import subprocess
from tqdm import tqdm
from PIL import Image, ImageDraw


def fetch_cards(set_url):
    """Fetch card titles and image urls from
    a mtg.design set url"""
    resp = requests.get(set_url)
    html = lxml.html.fromstring(resp.content)
    cards = html.cssselect('ul.index li')

    # Get card names and image urls
    return [(
        c.attrib['id'],
        c.cssselect('img')[0].attrib['data-original']
    ) for c in cards]


def prepare_card(im, save_path, corner_size=32, padding_size=40):
    """Prepare a card image by adding
    necessary bleed"""
    W, H = im.width, im.height
    draw = ImageDraw.Draw(im)

    # Fill in corners
    draw.rectangle(((0, 0), (CORNER_SIZE, CORNER_SIZE)), fill='black')
    draw.rectangle(((W-CORNER_SIZE, 0), (W, CORNER_SIZE)), fill='black')
    draw.rectangle(((0, H-CORNER_SIZE), (CORNER_SIZE, H)), fill='black')
    draw.rectangle(((W-CORNER_SIZE, H-CORNER_SIZE), (W, H)), fill='black')

    # Add padding/bleed
    card = Image.new('RGB', (W+PADDING_SIZE*2, H+PADDING_SIZE*2))
    card.paste(im, (PADDING_SIZE, PADDING_SIZE))

    # Save
    card.save(save_path, quality=100, dpi=(300, 300))


if __name__ == '__main__':
    import sys
    ZOOM = 2
    CORNER_SIZE = 32
    PADDING_SIZE = 40
    SET_URL = sys.argv[1]

    set_name = SET_URL.rsplit('/', 1)[-1]
    out_dir = os.path.join('cards', set_name)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    cards = fetch_cards(SET_URL)
    files = []
    for name, image_url in tqdm(cards):
        resp = requests.get(image_url)
        im = Image.open(io.BytesIO(resp.content))
        save_path = '{}/{}.jpg'.format(out_dir, name.lower().replace(' ', '_'))
        prepare_card(im, save_path,
                     corner_size=CORNER_SIZE,
                     padding_size=PADDING_SIZE)
        files.append(save_path)

    files = ['../{}'.format(f) for f in files]
    proc = subprocess.run(
        ['python', 'enhance.py', '--type=photo', '--zoom=2', '--device=gpu0'] + files,
        cwd='./neural-enhance'
    )