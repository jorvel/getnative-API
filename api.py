import getnative.app
import aiohttp
import gc
import os
from urllib.parse import urlparse
from vapoursynth import core
from pprint import pprint
from flask import Flask, request
from PIL import Image

core.add_cache = False
imwri = getattr(core, "imwri", getattr(core, "imwrif", None))
lossy = ["jpg", "jpeg", "gif"]
app = Flask(__name__)

@app.route("/", methods=['POST'])
async def getNative():
    # Todo: take optional parameters for getnative arguments
    url = request.form['url']
    filename = os.path.basename(urlparse(url).path)
    # Todo: take either image or URL to image
    # file = request.files['image']
    # filename = file.filename
    # img = Image.open(file.stream)

    # Todo, probably put some error handling here
    largs = [
        '--min-height', str(500),
        '--max-height', str(1080),
        '--aspect-ratio', str(0),
        '--kernel', str('bicubic'),
        '--bicubic-b', str('1/3'),
        '--bicubic-c', str('1/3'),
        '--lanczos-taps', str(3),
        '--stepping', str(1),
        '--output-dir', str("./"),
        '--plot-format', 'png',
    ]
    image = await get_image_as_videonode(url, './temp/', filename)
    # image = imwri.Read(img, float_output=True)

    try:
        import time
        start = time.time()
        best_value, _, getn = await getnative.app.getnative(largs, image, scaler=None)
        print('Time taken: ' + time.time() - start)
    except BaseException as err:
        print(err)
        raise err 

    gc.collect()
    content = ''.join([
        f"Output:"
        f"\n{getn.scaler}",
        f"\n{best_value}",
    ])

    return content


async def get_image_as_videonode(img_url, path, filename):
    image = await get_file(img_url, path, filename)
    if image is None:
        raise BaseException("Can't load image. Please try it again later.")

    return imwri.Read(image, float_output=True)

async def get_file(url, path, filename):
    async with aiohttp.ClientSession() as sess:
        async with sess.get(url) as resp:
            if resp.status != 200:
                return None
            with open(f"{path}/{filename}", 'wb') as f:
                f.write(await resp.read())
            return f"{path}/{filename}"
