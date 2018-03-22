from google.cloud import storage

class Bucket:

    def __init__(self, bucket_name):
        self.bucket_name = bucket_name
        self.connect_to_google_bucket()


    def connect_to_google_bucket(self):
        client = storage.Client()
        self.bucket = client.get_bucket(self.bucket_name)

    def google_bucket_listdir(self, prefix=None):
        #prefix is the directory-like thing, this will only list the things in that directory
        #and we will strip the directory, so it's just like a regular old boring listdir
        blob_list = self.bucket.list_blobs()
        if prefix:
            prefix = '/b/{}/o/{}%2F'.format(self.bucket_name,prefix)
        else:
            prefix = '/b/{}/o'.format(self.bucket_name)
        return [b.path.replace(prefix, '') for b in blob_list if b.path.startswith(prefix)]

    def open_google_file(self, path):
        blob = self.bucket.blob(path)
        return blob

def read_from_google_cloud(blob):
    contents = blob.download_as_string()
    return contents

def write_to_google_cloud(blob, contents, content_type=None):
    if content_type:
        blob.upload_from_string(contents, content_type=content_type)
    else:
        blob.upload_from_string(contents)