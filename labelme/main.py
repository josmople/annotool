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
    #     args.flags = ['0,Non-defect,非瑕疵,không khiếm khuyết', '-1,Others,其他,khác', '1,Hole,破洞,Vết bục vải - lủng lỗ', '2,End out,斷紗,Đứt sợi',
    #     '3,Accidental faulty,壞針,Kim hỏng', '6,Bar,橫條,Vải có vạch ngang', '7,Other fiber,異纖,Sợi sai-sợi bất thường', '8,Nep,棉結,Bết bông',
    #     '9,Needle line,針痕,Vết ren kim', '10,Rolling line,捲布痕,Lỗi do cuộn vải', '11,Oil,油污,Bẩn vết dầu', '12,Dirty,髒污,Vải bị bẩn',
    #     '13,Dye stain,色跡,Màu lỗi', '15,Crease mark,折痕,Vết gấp nếp', '16,Snag,鉤紗,Vết móc sợi', '17,Chaffed,擦痕,Vết chà sát',
    #     '18,Uneven dyeing,色花,Màu loang', '24,Over trimed,缺邊,Viền vải thiếu hụt', '30,Over selvage,針孔過入,Lỗ kim vào quá sâu',
    #     '31,Machine stop mark,停機痕,Lỗi do dừng máy', '32,接疋,Lỗi do đầu nối vải,Tack over piece', '35,Brush dirty,毛羽污染,Mặt lông bẩn',
    #     '39,掉毛屑未清除,Không vệ sinh bụi lông,Lossing fiber', '41,Haimess,起毛,Sủi lông (nổi lông)',
    #     '45,Press mark,壓痕,Vết  ép', '51,Angle,斜條,Sợi xiên', '52,Needle scratch,直條紋,đường sợi thẳng', '54,Wringkling fold,喂布痕,Vết nhăn vải',
    #     '57,crumpled,雞爪紋,Vết chân gà', '60,Split yam,裂紗,Tách sợi', '63,Oil needle,油針,Dầu kim',
    #     '64,Water trace(Water ripples),水痕(水波紋),Vết nước (vân bọt nước)', '68,Break OP,斷OP,"OP đứt ,giãn vỡ"', '70,Tangling,纏車,Rối màu',
    #     '75,Loose OP,OP鬆弛,OP Co giãn lỏng', '79,Thick & Thin Filling,粗細紗,"Sợi thô ,sợi nhỏ"', '161,Snag at back,暗鉤紗,Vết móc sợi ngầm',
    #     '181,Bleeding,滲色,Thẩm thấu màu', '453,Falling cloth indentation,落布壓痕,vết nhăn vải']
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
