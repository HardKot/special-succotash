#from scipy.integrate import quad
from math import exp, log
import decimal
import sqlite3


__GAZ__ = 'г'
__FUNCTIONCP__ = [0, 1, 0.5, -0.5, 2, -2, -1]
__DB__ = 'Chemistry.db'
__URLUI__ = 'UI/mobile.ui'

__R__ = 8.314


class Aggregations:
	def __init__(self, name, formuls):
		self.name = name
		self.parametrs = formuls.keys()
		self.formuls = formuls

	def foru(self, unknow):
		return self.formuls[unknow]
        
def CheckName(Name):
    for char in Name:
        if char in list(map(lambda i: str(i), range(10))):
            return False
    return True

def StrNumber(string):
    position = string.find(',')
    if position == -1:
        return int(string)
    integer = int(string[:position])
    fraction = int(string[position+1:]) + 0.1 - 0.1
    return integer + (fraction / 100) * integer / abs(integer)


class Substance:
    def __init__(self, Name, aggregation):
        if CheckName(Name):
            typeName = 'name'
        else:
            typeName = 'formula'
        
        with sqlite3.connect(__DB__) as db:
            c = db.cursor()
            c.execute('SELECT * FROM "substance" WHERE name=? AND state=?',
                      (Name, aggregation))
            r = c.fetchone()
        self.name, self.formula = r[1], r[2]
        self.H_f, self.S_f, self.G_f = StrNumber(
            r[4]) * 1000, StrNumber(r[6]), StrNumber(r[5]) * 1000
        self.state = aggregation
        self.Cp = StrNumber(r[7])


class System:
    def __init__(self, T, P, V, Substances):
        self.T = T
        self.P = P
        self.V = V
        self.substances = Substances
        self.Patm = P / 101300
    
    def processes(self, dT=0, dP=0, dV=0, dn=0):
        ''' dS = T * dQ ; dQ = dU + pdV + dW', dW' - работа химической реакции
        '''
        self.dT = dT
        self.dP = dP
        self.dV = dV

    def Work(self):
        if self.dP == 0:
            if self.dT == 0:
                self.dG = self.delta_H - self.T * self.delta_S
            else:
                self.dG = - (self.T + self.dT) * \
                    self.delta_S + self.T * self.delta_S
            return self.dG
        if self.dV == 0:
            if self.dT == 0:
                self.dF = self.delta_U - self.T * self.delta_S
            else:
                self.dF = - (self.T + self.dT) * \
                    self.delta_S + self.T * self.delta_S
            return self.dF

    def Reaction(self, coefficients):
        self.coefficients = {}
        for substance in self.substances.keys():
            self.coefficients[substance] = coefficients[substance.name]

    def recalculation(self):
        self.delta_Cp = 0
        self.delta_H = 0
        self.delta_S = 0
        for substance in self.substances.keys():
            self.delta_H += self.coefficients[substance] * substance.H_f
            self.delta_S += self.coefficients[substance] * substance.S_f
            self.delta_Cp += self.coefficients[substance] * substance.Cp
        if self.T != 298:
            self.delta_H += self.delta_Cp * quad(lambda T: pow(T, 0), 298, self.T)[0]
            self.delta_S += self.delta_Cp * quad(lambda T: pow(T, -1), 298, self.T)[0]
        
        """
        self.delta_Cp = [0] * len(__FUNCTIONCP__)        
        for i in range(len(__FUNCTIONCP__)):
            for substance in self.substances.keys():
                self.delta_Cp[i] += self.coefficients[substance] * substance.Cp[i]
        if self.T != 298:
            for i in range(len(__FUNCTIONCP__)):
                self.delta_H += self.delta_Cp[i] * quad(lambda T: pow(T, __FUNCTIONCP__[i]), 298, self.T)[0]
                self.delta_S += self.delta_Cp[i] * quad(lambda T: pow(T, __FUNCTIONCP__[i]-1), 298, self.T)[0]
        """
        
    def balance(self):
        self.Psubstances = {}
        Ngeneral = 0
        self.Kp = 1
        for Nsubstance in self.substances.values():
            Ngeneral += Nsubstance
        for substance in self.coefficients.keys():
            if substance.aggregation.name == __GAZ__:
                self.Psubstances[substance] = self.Patm * self.substances[substance] / Ngeneral
                self.Kp *= pow(self.Psubstances[substance], self.coefficients[substance])
        if self.dP == 0:
            lnKpT2 = self.dT * self.delta_H / (R * self.T * (self.T + self.dT)) + log(self.Kp)
            return decimal.Decimal(lnKpT2) ** decimal.Decimal(exp(1))
        return self.Kp, self.Psubstances
        
