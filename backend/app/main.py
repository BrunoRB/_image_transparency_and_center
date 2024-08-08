import requests
import os
import logging
from flask import Flask, flash, request, Blueprint
from werkzeug.utils import secure_filename
from PIL import Image, ImageOps
import numpy as np
from io import BytesIO

from flask_cors import CORS, cross_origin

app = Flask(__name__)
CORS(app, origins="*", support_credentials=True)  # Enable CORS for the entire app
# api = Blueprint('api', __name__, url_prefix='/api')

app.config["ROOT_FOLDER"] = os.path.dirname(os.path.abspath(__file__))
app.config["UPLOAD_FOLDER"] = "static/processing/"

app.secret_key = "some_secret_key"  # in a real app this would come from an ENV var

@app.route("/upload", methods=["POST"])

def upload_image():

    if "image" not in request.files:
        flash("No file part")
        return {"message": "No file part"}, 400
    file = request.files["image"]

    if not file.filename:
        return {"message": "No selected file"}, 400
    elif not "." in file.filename and file.filename.rsplit(".", 1)[1].lower() in [
        "png",
        "jpg",
        "jpeg",
        "gif",
    ]:
        return {"message": "Invalid file extension"}, 400

    filename = secure_filename(file.filename)
    file.save(_get_image_full_path_from_name(filename))

    return {
        "file_url": f"{request.url_root}{app.config['UPLOAD_FOLDER']}{filename}",
        "file_name": filename,
    }


@app.route("/apply-transparency", methods=["POST"])
def apply_transparency():
    """
    Based on the image from the request parameter
        and a selected color parameter
        apply transparency to the image
    """

    data = request.json

    image_name = data.get("image", "")
    color_rgb = data.get("color", "")
    if not image_name:
        return {"message": "No image selected"}, 400
    elif not color_rgb or not isinstance(color_rgb, list) or len(color_rgb) != 3:
        return {"message": "No color selected"}, 400

    color_rgb = tuple(color_rgb)

    logging.info(f"Processing image {image_name} with color {color_rgb}")

    image_url = f"{request.host_url}{app.config['UPLOAD_FOLDER']}{image_name}"

    response = requests.get(image_url)
    if response.status_code != 200:
        return {"message": f"Image not found {image_url}"}, 400

    image = Image.open(BytesIO(response.content))
    if image.mode != "RGBA":
        image = image.convert("RGBA")

    # Simply iterate over every pixel of the image, and set alpha to 0 if the color matches.
    # This could probably be done more efficiently using something like
    # https://pillow.readthedocs.io/en/stable/reference/Image.html#PIL.Image.composite
    # but here we are going for the simplest / more straightfoward solution
    for y in range(image.height):
        for x in range(image.width):
            current_color = image.getpixel((x, y))
            current_color = current_color[:3]
            if current_color == color_rgb:
                image.putpixel((x, y), current_color + (0,))

    image_name = image_name.rsplit(".", 1)[0] + ".png"

    filename = f"transparent_{image_name}"

    full_path = os.path.join(_get_image_full_path_from_name(filename))

    image.save(full_path)

    return {
        "file_url": f"{request.url_root}{app.config['UPLOAD_FOLDER']}{filename}",
        "file_name": filename,
    }

@app.route("/get-image-center", methods=["POST"])
def get_image_visual_center():
    data = request.json

    image_name = data.get("image")
    if not image_name:
        return {"message": "No image selected"}, 400

    image_path = _get_image_full_path_from_name(image_name)

    image = Image.open(image_path)
    if image.mode != "RGBA":
        image = image.convert("RGBA")

    if image.getchannel("A").getextrema() == (255, 255):
        return {"message": "Image has no transparency"}, 400

    image_data = np.array(image)

    alpha_channel = image_data[:, :, 3]
    transparent_mask = alpha_channel == 0

    grayscale_image = ImageOps.grayscale(image)
    image_array = np.array(grayscale_image, dtype=np.int64)
    image_array[transparent_mask] = 0

    min_intensity_diff = float("inf")
    best_center = (0, 0)

    for y in range(image.height):
        for x in range(image.width):
            top_left = np.sum(image_array[:y, :x])
            top_right = np.sum(image_array[:y, x:])
            bottom_left = np.sum(image_array[y:, :x])
            bottom_right = np.sum(image_array[y:, x:])

            intensity_diff = max(top_left, top_right, bottom_left, bottom_right) - min(
                top_left, top_right, bottom_left, bottom_right
            )

            if intensity_diff < min_intensity_diff:
                min_intensity_diff = intensity_diff
                best_center = (x, y)

        # break

    x_center, y_center = best_center

    # _mark_surrounding_pixels_and_save_image(
    #     image, int(x_center), int(y_center), f"center_{image_name}"
    # )

    return {
        "center": (x_center, y_center),
    }

def _get_image_full_path_from_name(image_name: str) -> str:
    return os.path.join(
        app.config["ROOT_FOLDER"],
        app.config["UPLOAD_FOLDER"],
        image_name,
    )


# utility debug function
def _mark_surrounding_pixels_and_save_image(
    img: Image, x_center: int, y_center: int, filename: str
):
    for y in range(y_center - 5, y_center + 5):
        for x in range(x_center - 5, x_center + 5):
            img.putpixel((x, y), (0, 255, 0, 255))

    full_path = os.path.join(_get_image_full_path_from_name(filename))
    img.save(full_path)


# app.register_blueprint(api)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
