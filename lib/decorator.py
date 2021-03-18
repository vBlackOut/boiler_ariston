from functools import wraps
import time

jours = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
mois = ["Janvier", u"Février", "Mars", "Avril", "Mai", "Juin", "Juillet", u"Août", "Septembre", "Octobre", "Novembre", " Décembre"]

def month_decrease(month, decrease_percent=0, temp="", change_output=False):
    def real_decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):

            args = list(args)

            if temp == args[3]:
                args[1] = args[1] - decrease_percent

            oldfunction = func(*args, **kwargs)

            if oldfunction > decrease_percent and change_output == True:
                begin_month = month.split('-')

                if "-" in month:
                    months = month.split('-')

                    position_begin = mois.index(months[0])
                    position_end = mois.index(months[-1])

                    if time.localtime()[1]-1 >= position_begin and time.localtime()[1]-1 <= position_end:
                        return oldfunction - decrease_percent
                    else:
                        return oldfunction

                else:
                    if mois[time.localtime()[1]-1] == month:
                        return oldfunction - decrease_percent
                    else:
                        return oldfunction
            else:
                return oldfunction

        return wrapper
    return real_decorator


def month_increase(month, increase_percent=0, temp="", change_output=False):
    def real_decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):

            args = list(args)

            if temp == args[3]:
                args[1] = args[1] - decrease_percent

            oldfunction = func(*args, **kwargs)

            if oldfunction > 0 and change_output == True:
                begin_month = month.split('-')

                if "-" in month:
                    months = month.split('-')

                    position_begin = mois.index(months[0])
                    position_end = mois.index(months[-1])

                    if time.localtime()[1]-1 >= position_begin and time.localtime()[1]-1 <= position_end:
                        return oldfunction + increase_percent
                    else:
                        return oldfunction

                else:
                    if mois[time.localtime()[1]-1] == month:
                        return oldfunction + increase_percent
                    else:
                        return oldfunction
            else:
                return oldfunction

        return wrapper
    return real_decorator
