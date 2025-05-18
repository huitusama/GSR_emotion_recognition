import pymysql


# connect database
def connect():
    db = pymysql.connect(
        host="localhost",
        user="root",
        password="yjw715901",
        db="PROJECT"
    )

    # 使用 cursor() 方法创建一个游标对象 cursor
    cursor = db.cursor()

    # 使用 execute() 方法执行 SQL，如果表存在则删除
    cursor.execute("DROP TABLE IF EXISTS EMOTION")

    # 使用预处理语句创建表
    sql = """CREATE TABLE EMOTION (
             `id` INT( 5 ) UNSIGNED NOT NULL ,
             `LIST` VARCHAR(255) NOT NULL ,
              PRIMARY KEY ( `id` )
              )"""

    cursor.execute(sql)

    # 关闭数据库连接
    db.close()


def insert(id, data):
    #db = pymysql.connect("localhost", "root", "yjw715901", "PROJECT")
    db = pymysql.connect(host="localhost", user="root", password="yjw715901", database="PROJECT")
    # 使用cursor()方法获取操作游标
    cursor = db.cursor()
    # SQL 插入语句
    sql = "INSERT INTO EMOTION(id, LIST) VALUES('%s','%s')" % (id, data)
    try:
        # 执行sql语句
        cursor.execute(sql)
        # 执行sql语句
        db.commit()
    except:
        # 发生错误时回滚
        print('insert error')
        db.rollback()
    finally:
        db.close()

# def insert(id, data):
#     try:
#         db = pymysql.connect(
#             host="localhost",
#             user="root",
#             password="yjw715901",
#             database="PROJECT",
#             autocommit=False  # 明确关闭自动提交
#         )
#         cursor = db.cursor()
#
#         # 使用参数化查询
#         sql = "INSERT INTO EMOTION(id, LIST) VALUES(%s, %s)"
#         affected = cursor.execute(sql, (id, data))
#
#         if affected == 1:
#             db.commit()
#             print(f"成功插入记录ID: {id}")
#         else:
#             db.rollback()
#             print(f"插入失败，影响行数: {affected}")
#
#     except pymysql.Error as e:
#         print(f"数据库操作失败: {e.args[1]}")  # 打印错误信息
#         db.rollback() if 'db' in locals() else None
#     finally:
#         db.close() if 'db' in locals() else None
