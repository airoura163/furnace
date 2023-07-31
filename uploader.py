# -*- coding: utf-8 -*-
# flake8: noqa

from qiniu import Auth, put_file, etag
import qiniu.config
from config import Config

config = Config()

ACCESS_KEY = config.env["QINIU"]["ACCESS_KEY"]
SECRET_KEY = config.env["QINIU"]["SECRET_KEY"]
EXTERNAL_DOMAIN = config.env["QINIU"]["EXTERNAL_DOMAIN"]
BUCKET_NAME = config.env["QINIU"]["BUCKET_NAME"]

class QiniuUploader:
    def __init__(self):
                
        #需要填写你的 Access Key 和 Secret Key
        self.access_key = ACCESS_KEY
        self.secret_key = SECRET_KEY
        # 外链
        self.URL = EXTERNAL_DOMAIN
        # 要上传的空间
        self.bucket_name = BUCKET_NAME
        # # 上传后保存的文件名
        # self.key = key
        # # 要上传文件的本地路径
        # self.localfile = localfile
        
    def upload(self, key, localfile):
        
        #构建鉴权对象
        q = Auth(self.access_key, self.secret_key)

        #生成上传 Token，可以指定过期时间等
        token = q.upload_token(self.bucket_name, key, 3600)
        
        ret, info = put_file(token, key, localfile, version='v2') 
        
        assert ret['key'] == key
        assert ret['hash'] == etag(localfile)
        
        if info.status_code == 200:
            return self.URL + key
        else:   
            return ''
