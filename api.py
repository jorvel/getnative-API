import getnative.app
import aiohttp
import gc
import os
from urllib.parse import urlparse
from vapoursynth import core
from pprint import pprint
from flask import Flask, request, abort, Response

core.add_cache = False
imwri = getattr(core, "imwri", getattr(core, "imwrif", None))
lossy = ["jpg", "jpeg", "gif"]
app = Flask(__name__)

@app.route("/", methods=['POST'])
async def getNative():
    # Get getnative args from form-data, or use defaults
    url = request.form.get('url', None)
    file = request.files.get('image', None)
    minHeight = request.form.get('min-height', 500)
    maxHeight = request.form.get('max-height', 1080)
    aspectRatio = request.form.get('aspect-ratio', 0)
    kernel = request.form.get('kernel', 'bicubic')
    bicubicB = request.form.get('bicubic-b', '1/3')
    bicubicC = request.form.get('bicubic-c', '1/3')
    lanczosTaps = request.form.get('lanczos-taps', 3)
    stepping = request.form.get('stepping', 1)

    largs = [
        '--min-height', str(minHeight),
        '--max-height', str(maxHeight),
        '--aspect-ratio', str(aspectRatio),
        '--kernel', str(kernel),
        '--bicubic-b', str(bicubicB),
        '--bicubic-c', str(bicubicC),
        '--lanczos-taps', str(lanczosTaps),
        '--stepping', str(stepping),
        '--output-dir', str("./"),
        '--plot-format', 'png',
    ]

    # Verify that we have either image or a URL to one
    if url is not None:
        filename = os.path.basename(urlparse(url).path)
        image = await get_image_as_videonode(url, './temp/', filename)
    elif file is not None:
        file.save('./temp/' + file.filename)
        filename = file.filename
        try:
            image = imwri.Read("./temp/" + filename, float_output=True)
        except BaseException as err:
            abort(Response(err,500))
            
    else:
        abort(Response('Missing image or URL',400))

    # Do error checking on parameters/image
    if os.path.splitext(filename)[1][1:] in lossy:
        abort(Response(f"Do not use lossy formats. Lossy formats are: {', '.join(lossy)}",400))
    
    # Use getnative to approximate native resolution
    try:
        best_value, _, getn = await getnative.app.getnative(largs, image, scaler=None)
    except BaseException as err:
        abort(Response(err,500))

    gc.collect()

    # Form output
    content = ''.join([
        f"Output:"
        f"\n{getn.scaler}",
        f"\n{best_value}",
    ])

    return content, 200


async def get_image_as_videonode(img_url, path, filename):
    image = await get_file(img_url, path, filename)
    if image is None:
        abort(Response("Can't load image. Please try it again later.",500))
    try:
        result = imwri.Read(image, float_output=True)
    except BaseException as err:
        abort(Response("Can't load image. Please try it again later.",500))

    return result 

async def get_file(url, path, filename):
    async with aiohttp.ClientSession() as sess:
        async with sess.get(url) as resp:
            if resp.status != 200:
                return None
            with open(f"{path}/{filename}", 'wb') as f:
                f.write(await resp.read())
            return f"{path}/{filename}"
