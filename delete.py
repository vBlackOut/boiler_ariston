from database import db

db.sqlite_db.drop_tables([db.Global_info], safe=True)
db.Global_info.create_table()

db.sqlite_db.drop_tables([db.Ballon1], safe=True)
db.Ballon1.create_table()

db.sqlite_db.drop_tables([db.Ballon2], safe=True)
db.Ballon2.create_table()
