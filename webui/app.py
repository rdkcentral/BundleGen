from gevent import monkey
monkey.patch_all()

from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_wtf import FlaskForm
from flask_socketio import SocketIO
from datetime import datetime
from wtforms import BooleanField, FileField, SelectField, StringField, TextAreaField
from werkzeug.utils import secure_filename

import glob
import os
import shutil
import json
import tarfile
import tempfile

from loguru import logger
from bundlegen.core.stb_platform import STBPlatform
from bundlegen.core.image_downloader import ImageDownloader
from bundlegen.core.image_unpacker import ImageUnpackager
from bundlegen.core.bundle_processor import BundleProcessor
from bundlegen.core.utils import Utils

TMP_DIR = '/tmp/bundlegen'
UPLOAD_FOLDER = '/tmp/uploads'
BUNDLE_STORE_DIR = '/bundlestore'

app = Flask(__name__)

# Generate a new secret key at startup for CSRF
SECRET_KEY = os.urandom(32)
app.config['SECRET_KEY'] = SECRET_KEY

socketio = SocketIO(app)

class AppError(Exception):
    # Generic exception handler
    status_code = 500

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv

class GenerateForm(FlaskForm):
    image_url = StringField()
    registry_uname = StringField()
    registry_password = StringField()
    uploaded_img = FileField()
    platform = SelectField()
    app_metadata = TextAreaField()
    lib_match = BooleanField()


def log_msg(msg):
    """Forward log messages over socketio
    """
    socketio.emit('consolelog', msg)

logger.add(log_msg, level='DEBUG', format="{level: <8}| {name} - {message}")

if not os.path.exists(TMP_DIR):
    os.makedirs(TMP_DIR)

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

if not os.path.exists(BUNDLE_STORE_DIR):
    os.makedirs(BUNDLE_STORE_DIR)


def get_templates():
    templates = glob.glob('../templates/**/*.json')

    selectItems = []

    for template in templates:
        if template.endswith('.json') and not template.endswith('_libs.json'):
            filename = os.path.basename(template)
            selectItems.append(filename.replace('.json', ''))

    return [(x, x) for x in selectItems]


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {"tar", "tar.gz"}


@app.errorhandler(AppError)
def handle_app_error(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.route('/', methods=["GET", "POST"])
def index():
    get_templates()
    form = GenerateForm()
    form.platform.choices = get_templates()

    if request.method == 'GET':
        return render_template('index.html', form=form)

    if form.validate_on_submit():
        print("Valid form submission")

        # Do BundleGen work
        outputdir = os.path.abspath(os.path.join(TMP_DIR, Utils.get_random_string(5)))
        selected_platform = STBPlatform(form.platform.data)

        if not selected_platform.found_config():
            print(f"Could not find config for platform {form.platform.data}")
            raise AppError("Could not find platform")

        img_url = ""
        creds = ""
        if form.image_url.data:
            # If downloading from URL, just use that as-is
            img_url = form.image_url.data
            # Add creds if given
            if form.registry_uname.data and form.registry_password.data:
                creds = f"{form.registry_uname.data}:{form.registry_password.data}"

        elif form.uploaded_img.data:
            # Got an uploaded image (hopefully a tar.gz!)
            f = form.uploaded_img.data
            filename = secure_filename(f.filename)
            upload_filepath = os.path.join(
                UPLOAD_FOLDER, filename
            )
            f.save(upload_filepath)

            # Extract tar
            # Extract the .tar to a temp directory
            img_temp_path = tempfile.mkdtemp()
            with tarfile.open(upload_filepath) as tar:
                tar.extractall(img_temp_path)

            # Delete tar
            os.remove(upload_filepath)

            img_url = f"oci:{img_temp_path}:latest"
            creds = None

        if not img_url:
            print("IMG URL is empty")
            raise AppError("Image URL cannot be empty")

        # Download Image
        img_downloader = ImageDownloader()
        img_path = img_downloader.download_image(
            img_url, creds, selected_platform.get_config())

        if not img_path:
            logger.error("Failed to donwload image")
            raise AppError("Image download failed")

        # Unpack the image with umoci
        tag = ImageDownloader().get_image_tag(img_url)
        img_unpacker = ImageUnpackager()
        img_unpacker.unpack_image(img_path, tag, outputdir)

        # Delete the downloaded image now we've unpacked it
        logger.info(f"Deleting {img_path}")
        shutil.rmtree(img_path)

        # Load app metadata
        app_metadata_image_path = os.path.join(
            outputdir, "rootfs", "appmetadata.json")
        image_metadata_exists = os.path.exists(app_metadata_image_path)

        app_metadata_dict = {}

        custom_app_metadata = form.app_metadata.data

        if not image_metadata_exists and not custom_app_metadata:
            # No metadata at all
            logger.error(
                f"Cannot find app metadata file in OCI image and none provided to BundleGen")
            raise AppError("No Metadata provided")
        elif (not image_metadata_exists and custom_app_metadata) or (image_metadata_exists and custom_app_metadata):
            # Use custom metadata
            app_metadata_dict = json.loads(custom_app_metadata)
        else:
            # Load metadata from image
            with open(app_metadata_image_path) as metadata:
                app_metadata_dict = json.load(metadata)

        # remove app metadata from image rootfs
        if image_metadata_exists:
            os.remove(app_metadata_image_path)

        # Begin processing. Work in the output dir where the img was unpacked to
        processor = BundleProcessor(
            selected_platform.get_config(), outputdir, app_metadata_dict, form.lib_match.data, "normal")
        if not processor.check_compatibility():
            # Not compatible - delete any work done so far
            shutil.rmtree(outputdir)
            raise AppError("App incompatible")

        success = processor.begin_processing()

        if not success:
            logger.warning("Failed to produce bundle")
            raise AppError("Something went wrong")

        tarball_name = app_metadata_dict["id"] + Utils.get_random_string(6)

        Utils.create_tgz(outputdir, tarball_name)
        logger.success(
            f"Successfully generated bundle at {tarball_name}.tar.gz")

        # Move to persistant storage
        print(f"Moving '{tarball_name}.tar.gz' to {BUNDLE_STORE_DIR}")
        shutil.move(f'{tarball_name}.tar.gz', BUNDLE_STORE_DIR)

        return jsonify(success=True)


@app.route('/bundles', methods=["GET"])
def get_bundles():
    # Return all the bundles in the store dir (we'll assume that dir is served by nginx or something)
    bundles = glob.glob(f'{BUNDLE_STORE_DIR}/*.tar.gz')
    bundles.sort(key=os.path.getmtime)

    filenames = [dict(zip(("name", "date", "size"), (os.path.basename(
        x), datetime.fromtimestamp(os.path.getmtime(x)), round(os.path.getsize(x) / 1024 / 1024, 2)))) for x in bundles]

    return jsonify(
        bundles=filenames
    )


@app.route('/bundle/<path:filename>', methods=["GET"])
def get_bundle(filename):
    return send_from_directory(BUNDLE_STORE_DIR, filename=filename)


if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0')