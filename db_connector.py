import mysql.connector
from mysql.connector import Error

def get_connection():
    try:
        connection = mysql.connector.connect(
            host="127.0.0.1",      # 远程服务器IP或域名，例如：rds.aliyuncs.com
            port=3306,                         # MySQL默认端口
            user="root",              # 数据库用户名
            password="yryyryA1",          # 数据库密码
            database="gsr_data",     # 数据库名称
            charset='utf8mb4'
        )
        return connection
    except Error as e:
        print("数据库连接失败：", e)
        return None
