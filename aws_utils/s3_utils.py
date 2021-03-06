
import io
import json
import zlib

import boto3
import dill as pickle

from .core import start_session


class s3_utils(object):
    """
    Aws Utility class for interfacing with S3

    Parameters
    ----------

    __init__ : key|string secret|string
       Initialize the class with AWS key and secret

    client : None
       Returns an S3 Client object for the low level API

    resource : None
       Returns a S3 Resource object for the high level API

    get_bucket : bucket_name|string
       Returns a bucket from S3

    get_bucket_key : bucket_name|string key_name|string
       Returns a key object from inside a bucket [file]

    get_bucket_key_json : None
       Use initialised bucket/key and creates an iterator to stream Json results line by line to not consume memory

    get_bucket_info : prefix|string
       Returns info of all objects with prefix from the current bucket

    to_s3 : bucket_name|string key_name|string
       Stores a python object as a compressed pickle

    from_s3 : bucket_name|str key_name|str
       Retrieves a pickle object from S3 uncompresses it and loads it as a python object

    from_bin_file_streaming : name|str[file_path] bucket_name|str key_name|str full_path|bool
       Takes a binary object from S3 and saves it on the filesystem under <name>

    from_bin_streaming : bucket_name|str key_name|str
       Returns a File buffer from a binary file in S3

    to_bin_streaming : data|Binary bucket_name|str key_name|str
       Binary Streaming data into S3 uses low memory

    read_bin : name|str[path] full_path|bool
       reads a binary file from filesystem using the same logic as from_bin_file_streaming

    iter_to_s3 : bucket_name|str iterable|iter key_name|str increments|int
       Stores any iterable into s3 in different increments to allow for reconstruction/function application

    """

    def __init__(self, key, secret, region_name="eu-west-1"):

        self.key = key
        self.secret = secret
        self.session = start_session(key, secret, region_name)
        self.client = self.session.client("s3")
        self.resource = self.session.resource("s3")

    def get_bucket(self, bucket_name):
        self.current_bucket = self.resource.Bucket(bucket_name)
        return self.current_bucket

    def get_bucket_key(self, bucket_name, key_name):
        self.current_bucket_key = self.client().get_object(
            Bucket=bucket_name, Key=key_name
        )
        return self.current_bucket_key

    def get_bucket_key_json(self):
        if hasattr(self, "current_bucket_key"):
            for i in self.current_bucket_key["Body"].iter_lines():
                yield json.loads(i.decode())
        else:
            print("No current bucket object initialized")

    def get_bucket_info(self, prefix):
        if hasattr(self, "current_bucket"):
            for obj in self.current_bucket.objects.filter(Prefix=prefix):
                print(obj.key, obj.size)
                yield obj
        else:
            print("Bucket has not yet been initialized")

    def to_s3(self, bucket_name, data, key_name):
        response = self.client().put_object(
            Bucket=bucket_name, Body=zlib.compress(pickle.dumps(data)), Key=key_name
        )
        return response

    def from_s3(self, bucket_name, key_name):
        return pickle.loads(
            zlib.decompress(
                self.client()
                .get_object(Bucket=bucket_name, Key=key_name)["Body"]
                .read()
            )
        )

    def from_bin_file_streaming(self, name, bucket_name, key_name, full_path=False):
        if full_path:
            path = name
        else:
            path = os.path.join(os.getcwd(), name)

        with open(path, "ab") as f:
            obj = (
                self.client()
                .get_object(Bucket=bucket_name, Key=key_name)["Body"]
                .iter_lines()
            )
            for i in obj:
                f.write(i)

    def from_bin_streaming(self, bucket_name, key_name):
        out_buffer = io.BytesIO()
        obj = (
            self.client
            .get_object(Bucket=bucket_name, Key=key_name)["Body"]
            .iter_chunks()
        )
        for i in obj:
            out_buffer.write(i)
        out_buffer.seek(0)
        return out_buffer

    def to_bin_streaming(self, data, bucket_name, key_name):
        out_buffer = io.BytesIO()
        out_buffer.write(data)
        out_buffer.seek(0)
        result = self.client().upload_fileobj(out_buffer, bucket_name, key_name)
        return result

    def read_bin(self, name, full_path=False):
        if full_path:
            path = name
        else:
            path = os.path.join(os.getcwd(), name)

        with open(path, "rb") as f:
            obj = f.read()
        return obj

    def iter_to_s3(self, bucket_name, iterable, key_name, increments=50):

        temp_list = []
        item_num = 0
        file_num = 0
        for item in iterable:
            item_num += 1
            print_iter(item_num)
            temp_list.append(item)
            if item_num != 0 and item_num % increments == 0:
                file_num += 1
                self.to_s3(bucket_name, temp_list, key_name + "_{}".format(file_num))
                temp_list = []

        if temp_list != []:
            self.to_s3(bucket_name, temp_list, key_name + "_{}".format(file_num + 1))

    def iter_bucket(self, bucket_name):
        for i in self.resource.Bucket(bucket_name).objects.all():
            yield i

    def get_s3_objects_containing(self, bucket_name, containing_string, gen=False):
        buckets = self.iter_bucket(bucket_name)

        if gen:
            for i in buckets:
                if containing_string in i.key:
                    yield i
        else:
            buckets = [i for i in buckets if containing_string in i.key]
            return buckets
