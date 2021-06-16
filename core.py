from math import exp, log
from decimal import Decimal
import sqlite3 as database

from scipy.integrate import quad
from scipy.misc import derivative

from options import __DB__, __FUNCTIONCP__, __GAZ__, __R__
from fixfunction import CheckName, StrNumber, StrFunction, universalDB, StrReaction

class Aggregations:
    def __init__(self, name):
        self.name = name
        result = universalDB("SELECT * FROM 'StateFunction' WHERE name={}", (self.name,))
        self.formul = result[0]
        self.type = result[2]
        result = universalDB("SELECT * FROM 'StateFunctionParametr' WHERE name={}", (name,))
        self.parametrFunction = {}
        for info in result:
            self.parametrFunction[info[1]] = {}
        for info in result:
            self.parametrFunction[info[1]][info[2]] = (info[3], info[4])
            
    def lambdaFunction(self, functions):
        self.parametrFunction = functions

class Elements:
    def __init__(self, symbol):
        result = universalDB('SELECT * FROM "PeriodicTable" WHERE symbol={}', (symbol,))
        self.id = result[0]
        self.name = result[1]
        self.mass = StrNumber(result[3])
        #* Добавил на всякий случай подсчет протоно и нейтронов
        self.proton = self.id
        self.neitron = round(self.mass) - self.proton
        # TODO : стоит ещё добавить заполненость валентной электронной орбитали
            
class Substance:
    def __init__(self, uid=None, name=None, formula=None, state=None, new=False, T=298):
        if new:
            lastId = universalDB(
                'SELECT seq FROM "sqlite_sequence" WHERE name="Substance"')[0][0]
            self.id = int(lastId) + 1
        else:
            if formula and not state:
                self.formula = formula
                uid = self.findStableSubstance(T)[0]
            if uid != None:
                result = universalDB(
                    'SELECT * FROM "Substance" WHERE id={}', (uid,))[0]
            else:
                if name:
                    result = universalDB(
                        'SELECT * FROM "Substance" WHERE name={} AND state={}', (name, state))[0]
                elif formula:
                    result = universalDB(
                        'SELECT * FROM "Substance" WHERE formula={} AND state={}', (formula, state))[0]
            #так как universalDB возвращает кортеж, даже если элемент один, то лучшим фиксом будет вернуть первый элемент
            self.id = result[0]
            self.name, self.formula, self.state = result[1], result[2], result[3]
            #так как universalDB возвращает кортеж, даже если элемент один, то лучшим фиксом будет вернуть первый элемент
            result = universalDB(
                'SELECT "dH", "S", "dG" FROM "TermodinamicParametrs" WHERE substance={}', (self.id,))[0]
            self.H_f, self.S_f, self.G_f = StrNumber(
                result[0]) * 1000, StrNumber(result[1]), StrNumber(result[2]) * 1000
            #так как universalDB возвращает кортеж, даже если элемент один, то лучшим фиксом будет вернуть первый элемент
            result = universalDB('SELECT * FROM "SubstanceCp" WHERE substance={}', (self.id,))[0]
            self.Cp = {}
            #* Cp(T) = T**0 + T**1 + T**0.5 + T**-0.5 + T**2 + T**-2 + T**-1
            for i in range(len(__FUNCTIONCP__)):
                self.Cp[__FUNCTIONCP__[i]] = StrNumber(result[i+1])
                
    def isComplex(self):
        for number in range(10):
            if self.formula.find(str(number)) + 1:
                return False
        return True
    
    def editionSubstanced(self, newname=None, newHF=None, newSF=None, newGF=None, newState=None, newFormula=None,newCp=None):
        if newname:
            universalDB('UPDATE "Substance" SET name={} WHERE id={}',
                        parametrs=(newname, str(self.id)), Commit=True)
        if newHF:
            universalDB('UPDATE "TermodinamicParametrs" SET dH={} WHERE Substance={}',
                        parametrs=(newHF, str(self.id)), Commit=True)
        if newSF:
            universalDB('UPDATE "TermodinamicParametrs" SET S={} WHERE Substance={}',
                        parametrs=(newSF, str(self.id)), Commit=True)
        if newGF:
            universalDB('UPDATE "TermodinamicParametrs" SET dG={} WHERE Substance={}',
                        parametrs=(newGF, str(self.id)), Commit=True)
        if newState:
            universalDB('UPDATE "Substance" SET state={} WHERE id={}',
                        parametrs=(newState, str(self.id)), Commit=True)
        if newFormula:
            universalDB('UPDATE "Substance" SET formula={} WHERE id={}',
                        parametrs=(newFormula, str(self.id)), Commit=True)
        if newCp:
            if type(newCp)==type(' '):
                universalDB('UPDATE "SubstanceCp" SET "T**0"={} WHERE Substance={}',
                            parametrs=(newCp, str(self.id)), Commit=True)
                for i in [1, 0.5, -0.5, 2, -2,-1]:
                    sql = 'UPDATE "SubstanceCp" SET "T**' + str(i) + '"="0" WHERE Substance={}'
                    universalDB(sql, parametrs=(
                        str(self.id),), Commit=True)
        
    def addSubstanced(self):
        universalDB('INSERT INTO "Substance"(id) VALUES ({})',
                    parametrs=(self.id,), Commit=True)
        universalDB('INSERT INTO "TermodinamicParametrs"(Substance) VALUES ({})',
                    parametrs=(self.id,), Commit=True)
        universalDB('INSERT INTO "SubstanceCp"(Substance) VALUES ({})',
                    parametrs=(self.id,), Commit=True)
    
    def findStableSubstance(self, T):
        substances = universalDB(
            'SELECT `id` FROM `Substance` WHERE `formula`={}', parametrs=(self.formula, ))
        substancesTP = {}
        for substance in substances:
            substancesTP[substance[0]] = universalDB(
                'SELECT `dH`, `S` FROM `TermodinamicParametrs` WHERE `Substance`={}', parametrs=(substance[0],))[0]
        temp = substancesTP.keys()
        ids = []
        for Id in temp:
            ids.append(Id)
        minG = StrNumber(substancesTP[ids[0]][0]) * 1000 - StrNumber(substancesTP[ids[0]][1]) * T
        idMinG = ids[0]
        ids.pop(0)
        for Id in ids:
            PminG = StrNumber(substancesTP[Id][0]) * \
                1000 - StrNumber(substancesTP[Id][1]) * T
            if PminG < minG:
                minG = PminG
                substance = id
        self.id = substance
        return self.id
        
class System:
    def __init__(self):
        self.T = 298
        self.P, self.Patm = 101300, 1
        self.V = 1
    
    def substanced(self, substanceds):
        self.substanceds = {}
        for substanced, coefficient in substanceds.items():
            self.substanceds[Substance(
                formula=substanced[0], state=substanced[1] if len(substanced[1]) > 0 else None, T=self.T)] = coefficient
        
         
    def startParametr(self, V, T=298, P=101300):
        """ Начальные значениея системы в единицах СИ(V[м^3], T[К], P[Па], n[Моль]), по умолчанию T=298, p=101.3кПа
        """
        # par: Substances = {<Объект вещество> : <его начальное количесвто>}
        self.T = T
        self.P, self.Patm = P, P / 101_300
        self.V = V


    def endParametr(self, T=None, P=None, V=None):
        '''Конечные параметры системы, в единицах СИ(V[м^3], T[К], P[Па], n[Моль]). Если пусто, то параметры все параметры являются константами
        '''
        self.dT = T - self.T
        self.dP = P - self.P
        self.dV = V - self.V

    def balance(self):
        self.Psubstances = {}
        Ngeneral = 0
        for substance, n in self.substances.items():
            if substance.aggregation == __GAZ__:
                Ngeneral += n
        # * dG0 = - R * T * lnKp => lnП[P(i)] = dG0 / - R * T, lnKp - lnKp
        self.Kp = 1
        lnKp = self.dG0 / - __R__ * self.T
        self.Kp = Decimal(exp(lnKp))
        if self.dG:
            lnProductP = 0
            # * dG = dG0 + R * T * lnП[P(i)]
            for substance, n in self.substances.items():
                if substance.aggregation == __GAZ__:
                    self.lnProductP *= pow((n * self.Patm / Ngeneral),
                                           self.coefficients[substance])

    def recalculation(self):
        self.delta_H = 0
        self.delta_S = 0
        self.delta_G0 = 0
        self.delta_Cp = {0: 0, 1: 0, 0.5: 0, -0.5: 0, 2: 0, -2: 0, -1: 0}
        for substance in self.substanceds.keys():
            self.delta_H += self.substanceds[substance] * substance.H_f
            self.delta_S += self.substanceds[substance] * substance.S_f
            self.delta_G0 += self.substanceds[substance] * substance.G_f

        #* Cp(T) = T**0 + T**1 + T**0.5 + T**-0.5 + T**2 + T**-2 + T**-1
            for i in __FUNCTIONCP__:
                self.delta_Cp[i] += self.substanceds[substance] * \
                    substance.Cp[i]
        if self.T != 298:
            for i in __FUNCTIONCP__:
                self.delta_H += self.delta_Cp[i] * \
                    quad(lambda T: pow(T, i), 298, self.T)[0]
                self.delta_S += self.delta_Cp[i]* \
                    quad(lambda T: pow(T, i - 1), 298, self.T)[0]
                self.delta_G0 -= self.delta_Cp[i] * \
                    quad(lambda T: pow(T, i - 1), 298, self.T)[0]
        
    def Work(self):
        self.work = {'deltaR_H': 0, 'deltaR_S' : 0}
        if self.dT:
            for i in __FUNCTIONCP__:
                self.work['deltaR_H'] += self.delta_Cp[i] * \
                    quad(lambda T: pow(T, i), self.T, self.T + self.dT)[0]
                self.work['deltaR_S'] += self.delta_Cp[i] * \
                    quad(lambda T: pow(T, i - 1), self.T, self.T + self.dT)[0]
            deltaG1 = self.delta_G0
            deltaG2 = self.work['deltaR_H'] - \
                (self.T + self.dT) * self.work['deltaR_S']
            self.work['deltaR_G'] = deltaG2 - deltaG1
        else:
            self.work = {'deltaR_H': self.delta_H, 'deltaR_S': self.delta_S, 'deltaR_G' : self.delta_G0}
        if self.dP:
            deltaH = 0
            for substance in self.substanceds.keys():
                if substance.state == '(г)':
                    deltaH = quad(lambda P: self.V, self.P, self.dP + self.P)[0]
            deltaS = deltaH / (self.T + self.dT)
            self.work['deltaR_H'] = self.work['deltaR_H'] + deltaH
            self.work['deltaR_S'] = self.work['deltaR_S'] + deltaS
            
            deltaG1 = self.work['deltaR_G']
            deltaG2 = deltaH - \
                (self.T + self.dT) * deltaS
            self.work['deltaR_G'] = deltaG2 - deltaG1
        if self.dV:
            deltaH = 0
            for substance in self.substanceds.keys():
                if substance.state == '(г)':
                    deltaH = quad(lambda V: self.P, self.V,
                                  self.dV + self.V)[0]
            deltaS = deltaH / (self.T + self.dT)
            self.work['deltaR_H'] = self.work['deltaR_H'] + deltaH
            self.work['deltaR_S'] = self.work['deltaR_S'] + deltaS

            deltaG1 = self.work['deltaR_G']
            deltaG2 = deltaH - \
                (self.T + self.dT) * deltaS
            self.work['deltaR_G'] = deltaG2 - deltaG1
