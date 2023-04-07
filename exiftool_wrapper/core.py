import ast
import subprocess
import shutil
from pathlib import Path
from datetime import datetime


class ExifToolWrapper:

    def __init__(self, file_path: str):
        # like a which command
        if shutil.which('exiftool') == None:
            raise Exception('Not found exiftool command..')
        self.file_path = Path(file_path)
        self.tags = self._get_exif()

    def _get_exif(self, fastopt: str = '-fast2') -> dict:
        if self.file_path.suffix in ['.cr2', '.CR2']:
            self.file_path = self.file_path.with_suffix('.xmp')
        # command string to list
        cmd = f"exiftool {fastopt} -json {self.file_path}".split()
        result = subprocess.run(cmd, stdout=subprocess.PIPE, text=True)
        exifjson = result.stdout.replace('\n', '').replace(
            'true', 'True').replace('false', 'False')
        # safe eval
        return ast.literal_eval(exifjson)[0]

    def get_camera_model(self, blank: bool = True) -> int:
        if self.tags is None:
            return 'NotFoundModel'
        if blank:
            return self.tags.get('Model')
        else:
            return self.tags.get('Model').replace(' ', '')

    def get_size(self) -> tuple:
        w = self.tags.get('ImageWidth')
        h = self.tags.get('ImageHeight')
        return (w, h)

    def which_orientation(self) -> str:
        w, h = self.get_size()
        if self.file_path.suffix in ['.jpg', '.JPG'] and 'Rotate' in self.tags.get('Orientation'):
            return 'portrait'
        elif self.file_path.suffix in ['.jpg', '.JPG'] and not 'Rotate' in self.tags.get('Orientation'):
            return 'landscape'
        elif self.file_path.suffix in ['.tif', '.TIF'] and w > h:
            return 'landscape'
        elif self.file_path.suffix in ['.tif', '.TIF'] and w < h:
            return 'portrait'
        else:
            raise Exception('orientaion error. no match')

    def get_adobe_rating(self) -> int:
        # ない場合は0
        return self.tags.get('Rating')

    def get_adobe_label(self) -> str:
        # ない場合はNone         
        return self.tags.get('Label')

    def get_timestamp(self, between: str = '.') -> str:
        # TODO いずれもない場合はファイル作成日を参照する。
        # yymmdd.hhmmss
        # 画像はexif datetime original, 動画はmedia createdateを参照する。
        exif_datetime_original = self.tags.get('DateTimeOriginal')
        media_create_date = self.tags.get('MediaCreateDate')
        file_modification_dt = self.tags.get('FileModifyDate')
        # tag check
        if not exif_datetime_original == None:
            d = exif_datetime_original
        elif not media_create_date in (None, '0000:00:00 00:00:00'):
            d = media_create_date
        elif not file_modification_dt == None:
            d = file_modification_dt.replace('+09:00', '')
        else:
            raise Exception('Not found datetime..')
        # parse dt
        dt = datetime.strptime(d, '%Y:%m:%d %H:%M:%S')
        return dt.strftime(f'%y%m%d{between}%H%M%S')
