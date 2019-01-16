import pymysql
import lambda_util

params = lambda_util.load_params("/rds/devdb/")
rds_host = params["host_url"]
user = params["username"]
password = params["password"]
db_name = params["aws_librarian_db_name"]


rdsi = None


def getRdsi():
    global rdsi
    if rdsi is None:
        rdsi = RDSInterface(rds_host, user, password, db_name)
    return rdsi


class BookReference(object):

    def __init__(self, tuple):
        self.id = tuple[0]
        self.series = tuple[1]
        self.name = tuple[2]
        self.path = tuple[3]
        self.dropbox_link = tuple[4]


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
