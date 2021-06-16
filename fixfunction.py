from sqlite3 import connect as database

from options import __DB__

from time import sleep

def CheckName(Name):
    for char in Name:
        if char in list(map(lambda i: str(i), range(10))):
            return False
    return True

def StrNumber(string):
    position_comma = string.find(',')
    position_dot = string.find('.')
    if position_comma == -1 and position_dot== -1:
        return int(string)
    position = position_dot if position_comma == -1 else position_comma
    integer = int(string[:position])
    fraction = int(string[position+1:]) + 0.1 - 0.1
    return integer + (fraction / 100) * integer / abs(integer)

def StrFunction(formuls):
    """ all = {
                     'MK': {'p': lambda V, n, T: pow(8.314, 1) * pow(n, 1) * pow(T, 1) * pow(V, -1),
                            'T': lambda P, V, n: P * V / (8.314 * n), 
                            'n': lambda T, V, P: P * V / (T * 8.314), 
                            'V': lambda P, T, n: 8.314 * n * T / P}
    }"""
    string = 'All = {\n'
    for formul in formuls.keys():
        string += ' ' * 6 + "\'{}\' : ".format(formul) + '{ \n'
        for parametr in formuls[formul]:
            string += ' ' * (len(formul) + 12) + '\'{}\' : lambda '.format(parametr)
            for subparametr in formuls[formul][parametr].keys():
                string += subparametr + ', '
            else:
                string = string[:-2] + ' : '
            for subparametr, i in formuls[formul][parametr].items():
                string+= ' {} * pow({}, {}) *'.format(i[0], subparametr, i[1])
            else:
                string = string[:-2] + ',\n'
        else:
            string = string[:-2] + '}'
    else:
        string += '\n}'
    with open('formuls.py', 'w') as file:
        file.write(string)
        
def StrSubstances(string):
    string = string.replace(' ', '')
    if string.find('->'):
        string.replace('->', '=')
    reaction = string
    substanseds = {}
    
def universalDB(sql, parametrs=None, Commit=False):
    with database(__DB__) as db:
        #Дальнейший код будет зависить от выбраной баззы данных, SQLite Значит используются кортежы и ?
        cursor = db.cursor()
        if parametrs:
            #print(sql.replace('{}', '?'), parametrs)
            sql = sql.replace('{}', '?')
            cursor.execute(sql, parametrs)
        else:
            cursor.execute(sql)
        if Commit:
            db.commit()
        result = cursor.fetchall()
    return result

def StrReaction(string):
    substanceds = {}
    reaction = string.replace('->', '=').replace(',', '.').replace(' ', '')
    initial = reaction[:reaction.find('=')] + '+'
    product = reaction[reaction.find('=')+1:] + '+'
    initial = PartReaction(initial)
    for substanced, coefficent in initial.items():
        substanceds[substanced] = -1 * StrNumber(coefficent)
    product = PartReaction(product)
    for substanced, coefficent in product.items():
        substanceds[substanced] = StrNumber(coefficent)
    return substanceds
    
def PartReaction(string):
    substanceds = {}
    while len(string) != 0:  # ! len(reaction)
        substanced = ''
        coefficent = ''
        state = ''
        if not string[0].isdigit():
            string = '1' + string
        i = string.find('+')
        for char in string[:i]:
            if not char.isdigit():
                break
            coefficent += char
        j = len(coefficent)
        for char in string[j:i]:
            if char in ['г', 'ж', 'т']:
                state = char
                break
            substanced += char
        string = string[i+1:]
        substanceds[(substanced, state)] = coefficent
    return substanceds