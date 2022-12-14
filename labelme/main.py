import argparse
import codecs
import logging
import os
import sys
import yaml

from PyQt5 import QtWidgets
sys.path.append("..")

from labelme import __appname__
from labelme import __version__
from labelme.app import MainWindow
from labelme.config import get_config
from labelme.logger import logger
from labelme.utils import newIcon

# from . import __appname__
# from . import __version__
# from app import MainWindow
# from config import get_config
# from logger import logger
# from utils import newIcon


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--version', '-V', action='store_true', help='show version'
    )
    parser.add_argument(
        '--reset-config', action='store_true', help='reset qt config'
    )
    parser.add_argument(
        '--logger-level',
        default='info',
        choices=['debug', 'info', 'warning', 'fatal', 'error'],
        help='logger level',
    )
    parser.add_argument('filename', nargs='?', help='image or label filename')
    parser.add_argument(
        '--output',
        '-O',
        '-o',
        help='output file or directory (if it ends with .json it is '
             'recognized as file, else as directory)'
    )
    default_config_file = os.path.join(os.path.expanduser('~'), '.labelmerc')
    parser.add_argument(
        '--config',
        dest='config_file',
        help='config file (default: %s)' % default_config_file,
        default=default_config_file,
    )
    # config for the gui
    parser.add_argument(
        '--nodata',
        dest='store_data',
        action='store_false',
        help='stop storing image data to JSON file',
        # default=argparse.SUPPRESS,
    )
    parser.add_argument(
        '--autosave',
        dest='auto_save',
        action='store_false',
        help='auto save',
        # default=argparse.SUPPRESS,
    )
    parser.add_argument(
        '--nosortlabels',
        dest='sort_labels',
        action='store_false',
        help='stop sorting labels',
        default=argparse.SUPPRESS,
    )
    parser.add_argument(
        '--flags',
        help='comma separated list of flags OR file containing flags',
        default='',
    )
    parser.add_argument(
        '--labelflags',
        dest='label_flags',
        help='yaml string of label specific flags OR file containing json '
             'string of label specific flags (ex. {person-\d+: [male, tall], '
             'dog-\d+: [black, brown, white], .*: [occluded]})',
        default=argparse.SUPPRESS,
    )
    parser.add_argument(
        '--labels',
        help='comma separated list of labels OR file containing labels',
        default=argparse.SUPPRESS,
    )
    parser.add_argument(
        '--validatelabel',
        dest='validate_label',
        choices=['exact', 'instance'],
        help='label validation types',
        default=argparse.SUPPRESS,
    )
    parser.add_argument(
        '--keep-prev',
        action='store_true',
        help='keep annotation of previous frame',
        default=argparse.SUPPRESS,
    )
    parser.add_argument(
        '--epsilon',
        type=float,
        help='epsilon to find nearest vertex on canvas',
        default=argparse.SUPPRESS,
    )
    args = parser.parse_args()

    if args.version:
        print('{0} {1}'.format(__appname__, __version__))
        sys.exit(0)

    logger.setLevel(getattr(logging, args.logger_level.upper()))

    # if hasattr(args, 'flags'):
    #     # if os.path.isfile(args.flags):
    #     #     with codecs.open(args.flags, 'r', encoding='utf-8') as f:
    #     #         args.flags = [l.strip() for l in f if l.strip()]
    #     # else:
    #     #     args.flags = [l for l in args.flags.split(',') if l]
    #     args.flags = ['0,Non-defect,?????????,kh??ng khi???m khuy???t', '-1,Others,??????,kh??c', '1,Hole,??????,V???t b???c v???i - l???ng l???', '2,End out,??????,?????t s???i',
    #     '3,Accidental faulty,??????,Kim h???ng', '6,Bar,??????,V???i c?? v???ch ngang', '7,Other fiber,??????,S???i sai-s???i b???t th?????ng', '8,Nep,??????,B???t b??ng',
    #     '9,Needle line,??????,V???t ren kim', '10,Rolling line,?????????,L???i do cu???n v???i', '11,Oil,??????,B???n v???t d???u', '12,Dirty,??????,V???i b??? b???n',
    #     '13,Dye stain,??????,M??u l???i', '15,Crease mark,??????,V???t g???p n???p', '16,Snag,??????,V???t m??c s???i', '17,Chaffed,??????,V???t ch?? s??t',
    #     '18,Uneven dyeing,??????,M??u loang', '24,Over trimed,??????,Vi???n v???i thi???u h???t', '30,Over selvage,????????????,L??? kim v??o qu?? s??u',
    #     '31,Machine stop mark,?????????,L???i do d???ng m??y', '32,??????,L???i do ?????u n???i v???i,Tack over piece', '35,Brush dirty,????????????,M???t l??ng b???n',
    #     '39,??????????????????,Kh??ng v??? sinh b???i l??ng,Lossing fiber', '41,Haimess,??????,S???i l??ng (n???i l??ng)',
    #     '45,Press mark,??????,V???t ????p', '51,Angle,??????,S???i xi??n', '52,Needle scratch,?????????,???????ng s???i th???ng', '54,Wringkling fold,?????????,V???t nh??n v???i',
    #     '57,crumpled,?????????,V???t ch??n g??', '60,Split yam,??????,T??ch s???i', '63,Oil needle,??????,D???u kim',
    #     '64,Water trace(Water ripples),??????(?????????),V???t n?????c (v??n b???t n?????c)', '68,Break OP,???OP,"OP ?????t ,gi??n v???"', '70,Tangling,??????,R???i m??u',
    #     '75,Loose OP,OP??????,OP Co gi??n l???ng', '79,Thick & Thin Filling,?????????,"S???i th?? ,s???i nh???"', '161,Snag at back,?????????,V???t m??c s???i ng???m',
    #     '181,Bleeding,??????,Th???m th???u m??u', '453,Falling cloth indentation,????????????,v???t nh??n v???i']
    if hasattr(args, 'labels'):
        if os.path.isfile(args.labels):
            with codecs.open(args.labels, 'r', encoding='utf-8') as f:
                args.labels = [l.strip() for l in f if l.strip()]
        else:
            args.labels = [l for l in args.labels.split(',') if l]

    if hasattr(args, 'label_flags'):
        if os.path.isfile(args.label_flags):
            with codecs.open(args.label_flags, 'r', encoding='utf-8') as f:
                args.label_flags = yaml.load(f)
        else:
            args.label_flags = yaml.load(args.label_flags)

    config_from_args = args.__dict__
    config_from_args.pop('version')
    reset_config = config_from_args.pop('reset_config')
    filename = config_from_args.pop('filename')
    output = config_from_args.pop('output')
    config_file = config_from_args.pop('config_file')
    config = get_config(config_from_args, config_file)

    if not config['labels'] and config['validate_label']:
        logger.error('--labels must be specified with --validatelabel or '
                     'validate_label: true in the config file '
                     '(ex. ~/.labelmerc).')
        sys.exit(1)

    output_file = None
    output_dir = None
    if output is not None:
        if output.endswith('.json'):
            output_file = output
        else:
            output_dir = output

    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName(__appname__)
    app.setWindowIcon(newIcon('icon'))
    win = MainWindow(
        config=config,
        filename=filename,
        output_file=output_file,
        output_dir=output_dir,
    )

    if reset_config:
        logger.info('Resetting Qt config: %s' % win.settings.fileName())
        win.settings.clear()
        sys.exit(0)

    win.show()
    win.raise_()
    sys.exit(app.exec_())


# this main block is required to generate executable by pyinstaller
if __name__ == '__main__':
    main()
