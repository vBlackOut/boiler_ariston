from peewee import *
import datetime

#sqlite_db = SqliteDatabase('/home/pi/Python/ADS/database/database.db', pragmas={'journal_mode': 'wal'})
sqlite_db = MySQLDatabase("chaufeau", host="127.0.0.1", port=3306, user="root", passwd="")

class Ballon1(Model):
    Sonde_haut = FloatField(null=True)
    Sonde_bas = FloatField(null=True)
    moyenne_temperature = FloatField(null=True)
    resistance = IntegerField(null=True)
    watt = IntegerField(null=True)
    date = DateTimeField()

    def save(self, *args, **kwargs):
        self.date = datetime.datetime.now()
        super(Ballon1, self).save(*args, **kwargs)

    class Meta:
        database = sqlite_db
        db_table = 'Ballon1'

class Ballon2(Model):
    Sonde_haut = FloatField(null=True)
    Sonde_bas = FloatField(null=True)
    moyenne_temperature = FloatField(null=True)
    resistance = IntegerField(null=True)
    watt = IntegerField(null=True)
    date = DateTimeField()

    def save(self, *args, **kwargs):
        self.date = datetime.datetime.now()
        super(Ballon2, self).save(*args, **kwargs)

    class Meta:
        database = sqlite_db
        db_table = 'Ballon2'

class Global_info(Model):
    flow = FloatField(null=True)
    sonde_interne = FloatField(null=True)
    date = DateTimeField()
    rend_ballon1 = FloatField(null=True)
    rend_ballon2 = FloatField(null=True)


    def save(self, *args, **kwargs):
        self.date = datetime.datetime.now()
        super(Global_info, self).save(*args, **kwargs)

    class Meta:
        database = sqlite_db
        db_table = 'Global_info'

class Conso_info(Model):
    volt = FloatField(null=True)
    ampere = FloatField(null=True)
    va = FloatField(null=True)
    watt = FloatField(null=True)
    kwh = FloatField(null=True)
    power = BooleanField(null=True)
    date = DateTimeField()


    def save(self, *args, **kwargs):
        self.date = datetime.datetime.now()
        super(Conso_info, self).save(*args, **kwargs)

    class Meta:
        database = sqlite_db
        db_table = 'Conso_info'

sqlite_db.connect()
#Conso_info.create_table()
# Ballon1.create_table()
# Ballon2.create_table()
