import boto3
import os
import json
import dropbox
import pymysql

client = boto3.client(
    'ssm',
    region_name='us-east-2',
    aws_access_key_id=os.getenv("AWS_Key_Id"),
    aws_secret_access_key=os.getenv("AWS_Secret"))


def load_params(path):
    param_details = client.get_parameters_by_path(
        Path=path,
        Recursive=False,
        WithDecryption=True
    )

    toReturn = {}

    for param_info in param_details["Parameters"]:
        toReturn[param_info["Name"][len(path):]] = param_info["Value"]

    return toReturn


class BookReference(object):

    def __init__(self, tuple):
        self.id = tuple[0]
        self.series = tuple[1]
        self.name = tuple[2]
        self.path = tuple[3]
        self.dropbox_link = tuple[4]

    def __repr__(self):
        return "<BookReference id:{id}> {series}-{name}; {path}; {link}".format(
            id=self.id,
            name=self.name,
            series=self.series,
            path=self.path,
            link=self.dropbox_link
        )


class RDSInterface(object):

    def __init__(self, rds_host, user, password, db_name):
        self.conn = pymysql.connect(rds_host, user=user,
                                    passwd=password, db=db_name, connect_timeout=5)

    def query_name(self, name_substring):
        cur = self.conn.cursor()
        sql = "select * from raw_dropbox where name like %s OR series like %s"

        cur.execute(sql, [('%' + name_substring + '%'),
                          ('%' + name_substring + '%')])

        data = cur.fetchall()
        cur.close()

        return [BookReference(x) for x in data]

    def insert_or_update(self, list_of_tuples):
        cur = self.conn.cursor()

        # "INSERT INTO raw_dropbox (name, path, series, dropbox_link) VALUES (%s, %s, %s, %s)"
        sql = '''INSERT INTO raw_dropbox (name, path, series, dropbox_link)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
        path = %s,
        series = %s,
        dropbox_link =%s;'''

        expanded_tuples = [(x[0], x[1], x[2], x[3], x[1], x[2], x[3])
                           for x in list_of_tuples]
        cur.executemany(sql, expanded_tuples)

        cur.close()


def remove_prefix(text, prefix):
    if text.startswith(prefix):
        return text[len(prefix):]
    return text


class DropboxInterface(object):

    def __init__(self, access_token):
        self.dbx = dropbox.Dropbox(access_token)

    def get_direct_download_link(self, path):
        shared_link_metadata = self.dbx.sharing_create_shared_link(
            path, short_url=False)
        # replacing dl=0 to dl=1, changes it from a website, to a direct dowload to a file/zip of a folder
        return shared_link_metadata.url.replace("dl=0", "dl=1")

    def get_folder_metadata(self, path):
        def isFolder(metaData):
            return isinstance(metaData, dropbox.files.FolderMetadata)

        folders = set()
        self.folder_iterator(path, None, isFolder, folders)

        return folders

    def organize_into_folders(self, folders, root_path):
        root_path = root_path.lower()
        organized_folders = dict()

        # we assume folders is sorted
        for folder_path in folders:
            folder_name = remove_prefix(folder_path, root_path + "/")
            path_parts = folder_name.split("/")
            if len(path_parts) == 1:
                organized_folders[path_parts[0]] = folder_path
            else:
                series_name = path_parts[0]
                book_name = path_parts[1]

                if not isinstance(organized_folders[series_name], dict):
                    organized_folders[series_name] = dict()
                organized_folders[series_name][book_name] = folder_path

        return organized_folders

    def generator_book_tuples_from_organized_folders(self, organized_folders):
        def gen_book_tuple(name, path, series, dropbox_download):
            return (series, name, dropbox_download, path)

        for k, v in organized_folders.items():
            if isinstance(v, dict):
                for kk, vv in v.items():
                    yield gen_book_tuple(name=kk, path=vv, series=k, dropbox_download=self.get_direct_download_link(vv))
            else:
                yield gen_book_tuple(name=k, path=v, series=None, dropbox_download=self.get_direct_download_link(v))

        return

    def folder_iterator(self, path, cursor, conditional, objects):
        if cursor is None:
            results = self.dbx.files_list_folder(path, recursive=False)
        else:
            results = self.dbx.files_list_folder_continue(cursor)

        for metaData in results.entries:
            if conditional(metaData):
                objects.add(metaData)
                self.folder_iterator(metaData.path_lower, None,
                                     conditional, objects)

        if results.has_more:
            self.folder_iterator(path, results.cursor, conditional, objects)

        return

    def get_book_tuples(self, path):
        tuples = list()
        folders = self.get_folder_metadata(path)
        folder_paths = [folder.path_lower for folder in folders]
        folder_paths.sort()
        organized_folders = self.organize_into_folders(folder_paths, path)
        for val in self.generator_book_tuples_from_organized_folders(organized_folders):
            tuples.append(val)

        return tuples


if __name__ == "__main__":
    print("booting up")
    db_access_token = load_params("/dropbox/")['access_token']
    dbi = DropboxInterface(db_access_token)
    print("dropbox connected")
    sources = json.loads(os.getenv('AUDIOBOOK_SOURCES'))

    db_params = load_params("/rds/devdb/")
    rdsi = RDSInterface(rds_host=db_params['host_url'],
                        user=db_params['username'],
                        password=db_params['password'],
                        db_name=db_params['aws_librarian_db_name'])

    print("rds connected")

    print(rdsi.query_name("mistborn"))

    tuples = list()
    for path in sources:
        tuples.extend(dbi.get_book_tuples(path))
        print("done getting names for " + path)

    print(len(tuples))

    rdsi.insert_or_update(tuples)
