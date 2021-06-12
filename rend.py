from database import db
from datetime import datetime
from datetime import timedelta
from numpy import mean as avg

def rendement(minute):
    date = datetime.now()
    date_range = date - timedelta(seconds = minute)

    query = db.Ballon1.select().order_by(db.Ballon1.id.desc()).where(db.Ballon1.date.between(date_range, date))
    Sonde = [row.moyenne_temperature for row in query if row.moyenne_temperature != None and row.date != None or row.moyenne_temperature != None and row.date != None]
    if (Sonde[-1]-avg(Sonde) <= 0):
        Sonde_rend1 = (max(Sonde) - min(Sonde)) / minute
    else:
        Sonde_rend1 = -(max(Sonde) - min(Sonde)) / minute

    if round(Sonde_rend1*60,2) < 7:
        print("Estimation Ballon 1 Entrer : -{}°C par heures".format(round(Sonde_rend1*60,2)))
    else:
        print("Estimation Ballon 1 Entrer : Calcule en cours...".format(round(Sonde_rend1*60,2)))

    query = db.Ballon2.select().order_by(db.Ballon2.id.desc()).where(db.Ballon2.date.between(date_range, date))
    Sonde = [row.moyenne_temperature for row in query if row.moyenne_temperature != None and row.date != None or row.moyenne_temperature != None and row.date != None]
    if (Sonde[-1]-avg(Sonde) <= 0):
        Sonde_rend2 = (max(Sonde) - min(Sonde)) / minute
    else:
        Sonde_rend2 = -(max(Sonde) - min(Sonde)) / minute

    if round(Sonde_rend2*60,2) < 7:
        print("Estimation Ballon 2 Sortie: {}°C par heures\n".format(round(Sonde_rend2*60,2)))
        return round(Sonde_rend2*60,2)
    else:
        print("Estimation Ballon 2 Sortie: Calcule en cours...\n".format(round(Sonde_rend2*60,2)))
        return None

    #db_save = db.Global_info.create(rend_ballon1=Sonde_rend1 * minute, rend_ballon2=Sonde_rend2 * minute, date=date)
    #db_save.save()


rendement(30)
