import os
from storages.backends.s3boto3 import S3Boto3Storage
class MediaStorage(S3Boto3Storage):
    bucket_name = 'gpodder-statics'
    location = 'uploads'

class StaticStorage(S3Boto3Storage):
    bucket_name = 'gpodder-statics'
    location = 'statics'
