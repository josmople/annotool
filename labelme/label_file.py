import base64
import io
import json
import os.path as osp
import os
from shutil import ExecError
import PIL.Image

from labelme._version import __version__
from labelme.logger import logger
from labelme import PY2
from labelme import QT4
from labelme import utils


class LabelFileError(Exception):
    pass


class LabelFile(object):

    suffix = '.json'

    def __init__(self, filename=None):
        self.shapes = ()
        self.imagePath = None
        self.imageData = None
        print("labelinit", filename)
        if filename is not None:
            self.load(filename)
        self.filename = filename

    @staticmethod
    def load_image_file(filename):
        try:
            image_pil = PIL.Image.open(filename)
            print("load_image", filename)
        except IOError:
            logger.error('Failed opening image file: {}'.format(filename))
            return

        # apply orientation to image according to exif
        image_pil = utils.apply_exif_orientation(image_pil)

        with io.BytesIO() as f:
            ext = osp.splitext(filename)[1].lower()
            if PY2 and QT4:
                format = 'PNG'
            elif ext in ['.jpg', '.jpeg']:
                format = 'JPEG'
            else:
                format = 'PNG'
            image_pil.save(f, format=format)
            f.seek(0)
            return f.read()

    def load(self, filename):
        keys = [
            'imageData',
            'imagePath',
            'lineColor',
            'fillColor',
            'shapes',  # polygonal annotations
            'flags',   # image level flags
            'imageHeight',
            'imageWidth',
        ]
        try:
            with open(filename, 'rb' if PY2 else 'r', encoding="utf-8") as f:
                data = json.load(f)
            # if data['imageData'] is not None:
            #    imageData = base64.b64decode(data['imageData'])
            #    if PY2 and QT4:
            #        imageData = utils.img_data_to_png_data(imageData)
            # else:
            # relative path from label file to relative path from cwd
            print("load1", osp.dirname(filename))
            print("load2", data['imagePath'])
            imagePath = osp.join(osp.dirname(filename), osp.basename(data['imagePath']).split('\\')[-1]).replace("labels/", "").replace('labels\\', "")
            self.imagePath = imagePath
            data['imagePath'] = imagePath
            print("load3", self.imagePath)
            imageData = self.load_image_file(imagePath)
            flags = data.get('flags') or {}
            imagePath = data['imagePath']
            self._check_image_height_and_width(
                base64.b64encode(imageData).decode('utf-8'),
                data.get('imageHeight'),
                data.get('imageWidth'),
            )
            lineColor = data['lineColor']
            fillColor = data['fillColor']
            lineColor = None
            fillColor = None
            shapes = []

            shapes = (
                (
                    s['label'],
                    s['points'],
                    s['line_color'],
                    s['fill_color'],
                    s.get('shape_type', 'polygon'),
                    s.get('flags', {}),
                    s['remarks'] if 'remarks' in s else None,
                    s['state_label'] if 'state_label' in s else None,
                    s['isUnsure'] if 'isUnsure' in s else False,
                    s['isScannerIssue'] if 'isScannerIssue' in s else False,
                    s['isLowResolution'] if 'isLowResolution' in s else False,
                    s['species'] if 'species' in s else None,
                )
                for s in data['shapes']
            )

        except Exception as e:
            raise LabelFileError(e)

        otherData = {}
        for key, value in data.items():
            if key not in keys:
                otherData[key] = value

        # Only replace data after everything is loaded.
        self.flags = flags
        self.shapes = shapes
        self.imagePath = imagePath
        print("LOAD4", self.imagePath, imagePath)
        self.imageData = imageData
        self.lineColor = lineColor
        self.fillColor = fillColor
        self.filename = filename
        self.otherData = otherData

    @staticmethod
    def _check_image_height_and_width(imageData, imageHeight, imageWidth):
        img_arr = utils.img_b64_to_arr(imageData)
        if imageHeight is not None and img_arr.shape[0] != imageHeight:
            logger.error(
                'imageHeight does not match with imageData or imagePath, '
                'so getting imageHeight from actual image.'
            )
            imageHeight = img_arr.shape[0]
        if imageWidth is not None and img_arr.shape[1] != imageWidth:
            logger.error(
                'imageWidth does not match with imageData or imagePath, '
                'so getting imageWidth from actual image.'
            )
            imageWidth = img_arr.shape[1]
        return imageHeight, imageWidth

    def save(
        self,
        filename,
        imagePath,
        flags=None,
        shapes=None,
        imageHeight=None,
        imageWidth=None,
        imageData=None,
        lineColor=None,
        fillColor=None,
        otherData=None,
    ):
        if imageData is not None:
            imageData = base64.b64encode(imageData).decode('utf-8')
            imageHeight, imageWidth = self._check_image_height_and_width(
                imageData, imageHeight, imageWidth
            )
        if otherData is None:
            otherData = {}
        if flags is None:
            flags = {}
        data = dict(
            # version=__version__,
            flags=flags,
            shapes=shapes,
            lineColor=lineColor,
            fillColor=fillColor,
            imagePath=imagePath,
            # imageData=imageData,
            # imageHeight=imageHeight,
            # imageWidth=imageWidth,
        )

        for key, value in otherData.items():
            data[key] = value
        try:
            print("1", filename)
            print(data["imagePath"])
            if 'labels' not in filename:
                filename = osp.join(osp.join(osp.dirname(filename), 'labels'), osp.basename(filename))
                print("2", filename)
                os.makedirs(osp.dirname(filename), exist_ok=True)
            with open(filename, 'wb' if PY2 else 'w', encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.filename = filename
        except Exception as e:
            raise LabelFileError(e)

    @staticmethod
    def is_label_file(filename):
        return osp.splitext(filename)[1].lower() == LabelFile.suffix
