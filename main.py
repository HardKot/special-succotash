import sys

from PyQt5 import QtWidgets, uic, QtCore
from PyQt5.QtWidgets import QTableWidgetItem


from core import Substance, Aggregations, System
from UI.mobile import Ui_MainWindow
from fixfunction import universalDB, StrFunction, StrReaction, StrNumber
from functools import partial
from formuls import All

class mobile(QtWidgets.QMainWindow):
    def __init__(self):
        super(mobile, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        #self.ui.FindS.clicked.connect(self.findDateSubstance)
        self.ui.FindName.textChanged.connect(self.findSubstanceName)
        self.ui.FindFormula.textChanged.connect(self.findSubstanceFormula)
        self.ui.backFindDB.clicked.connect(self.clearInfoSubstance)
        self.ui.ClearFind.clicked.connect(self.clearFindSubstance)
        self.ui.EditionSubstance.clicked.connect(self.editionSubstance)
        self.ui.SaveEditionSubstance.clicked.connect(self.saveEditionSubstance)
        self.ui.NewSubstanced.clicked.connect(self.NewSubstenced)
        self.showFindSubstanceds()
        self.ui.ReactionCalculation.clicked.connect(self.ShowCalculation)
        self.ui.BackCalculation.clicked.connect(self.closeCalculation)
        self.ui.Calculation.clicked.connect(self.CalculatReaction)
        
        
        #! - перенести на продакшане
        self.ui.SubstancesInfo.hide()
        self.ui.SaveEditionSubstance.hide()
        self.ui.SubstanceStateEdition.hide()
        self.ui.EditNameSubstance.hide()
        self.ui.CancleEditionSubstance.hide()
        self.ui.FindSubstances.resizeColumnsToContents()
        self.ui.FindSubstances.setColumnWidth(2, 10)
        
        self.ui.EditionSubstanceHF.hide()
        self.ui.EditionSubstanceSF.hide()
        self.ui.EditionSubstanceGF.hide()
        self.ui.newFomula.hide()
        self.ui.Formula.hide()
        
        self.ui.NewSubstenced.hide()
        self.ui.CancleNewSubstance.clicked.connect(self.closeNewSubstenced)
        self.ui.SaveNewSubstance.clicked.connect(self.createNewSubstenced)
        
        self.ui.System.hide()
        self.ui.ResultReaction.hide()
        
        #!
    
    def ShowCalculation(self):
        self.ui.System.show()
        self.ui.FindSubstancesDb.hide()
    
    def CalculatReaction(self):
        string = self.ui.Substanced.text()
        reactor = System()
        reactor.substanced(StrReaction(string))
        parametr = {'T': [self.ui.StartTemperatura.text() if self.ui.StartTemperatura.text().replace(' ', '') else '298', ],
                    'P': [self.ui.StartPressure.text() if self.ui.StartPressure.text().replace(' ', '') else '101300', ],
                    'S': [self.ui.StartSize.text() if self.ui.StartSize.text().replace(' ', '') else '1', ],
                    }
        reactor.startParametr(V=StrNumber(parametr['S'][0]), P=StrNumber(parametr['P'][0]), T=StrNumber(parametr['T'][0]))
        if self.ui.ConstPressure.isChecked() : 
            parametr['P'].append(parametr['P'][0])
        else:
            if len(self.ui.EndPressure.text().replace(' ', '')) == 0:
                # Написать ошибку
                return
            parametr['P'].append(self.ui.EndPressure.text().replace(' ', ''))
            
        if self.ui.ConstSize.isChecked() :
            parametr['S'].append(parametr['S'][0])
        else:
            if len(self.ui.EndSize.text().replace(' ', '')) == 0:
                # Написать ошибку
                return
            parametr['S'].append(self.ui.EndSize.text().replace(' ', ''))
            
        if self.ui.ConstTemeratura.isChecked():
            parametr['T'].append(parametr['T'][0])
        else:
            if len(self.ui.EndTemperatura.text().replace(' ', '')) == 0:
                # Написать ошибку
                return
            parametr['T'].append(self.ui.EndTemperatura.text().replace(' ', ''))

        reactor.endParametr(
            V=StrNumber(parametr['S'][1]), P=StrNumber(parametr['P'][1])
                        , T=StrNumber(parametr['T'][1]))
        reactor.recalculation()
        reactor.Work()
        self.ui.ResultReaction.show()
        self.ui.dH.setText(
            "{:.3f} кДж".format(reactor.work['deltaR_H'] / 1000))
        self.ui.dS.setText(
            "{:.3f} Дж/Т".format(reactor.work['deltaR_S']))
        self.ui.dG.setText(
            "{:.3f} кДж".format(reactor.work['deltaR_G'] / 1000))
        
        
    def closeCalculation(self):
        self.ui.Reaction.hide()
        self.ui.FindSubstancesDb.show()
        
    def showFindSubstanceds(self, optional=''):
        try:
            substances = universalDB(
                'SELECT * FROM "Substance" {} ORDER BY name'.format(optional))
        except:
            pass
        else:
            i = 0
            self.ui.FindSubstances.setRowCount(len(substances))
            for substance in substances:
                row = []
                for j in range(1,4):
                    col = QTableWidgetItem(substance[j])
                    col.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
                    self.ui.FindSubstances.setItem(
                        i, j-1, QTableWidgetItem(col))
                button = QtWidgets.QPushButton('Кнопочка', self)
                button.clicked.connect(
                    partial(self.showInfoSubstance, id=substance[0]))
                self.ui.FindSubstances.setCellWidget(i, 3, button)
                i += 1
         
    def findSubstanceName(self):
        self.ui.FindSubstances.clearContents()
        self.showFindSubstanceds(optional='WHERE name LIKE "{}%"'.format(
            self.ui.FindName.text()))
        
    def findSubstanceFormula(self):
        self.ui.FindSubstances.clearContents()
        self.showFindSubstanceds(optional='WHERE formula LIKE "%{}%"'.format(
            self.ui.FindFormula.text()))
        
    def showInfoSubstance(self, id):
        self.ui.SubstancesInfo.show()
        self.ui.FindSubstancesDb.hide()
        substance = Substance(uid=id)
        title = '{}{} -> {}'.format(substance.name, substance.state, substance.formula)
        self.ui.NameFormulSubstance.setText(title)
        self.ui.idsubstance.hide()
        self.ui.idsubstance.setText(str(substance.id))
        self.ui.EditNameSubstance.setText(substance.name)
        self.ui.SubstanceHF.setText(str(substance.H_f / 1000))
        self.ui.SubstanceSF.setText(str(substance.S_f))
        self.ui.SubstanceGF.setText(str(substance.G_f / 1000))
        strCP = ''
        for logT, cp in substance.Cp.items():
            if cp == '0':
                continue
            if logT == 0:
                strCP += str(cp) + ' + '
            else:
                strCP += '{}T^{} + '.format(cp, logT)
        else:
            strCP = strCP[:-2]    
        self.ui.SubstanceCp.setText(str(substance.H_f))
        self.ui.CancleEditionSubstance.clicked.connect(self.cancleEdition)
        
    def clearInfoSubstance(self):
        self.ui.SubstancesInfo.hide()
        self.ui.FindSubstancesDb.show()
    
    def clearFindSubstance(self):
        self.ui.FindSubstances.clearContents()
        self.ui.FindFormula.clear()
        self.ui.FindName.clear()
        self.showFindSubstanceds()

    def editionSubstance(self):
        self.ui.SaveEditionSubstance.show()
        self.ui.SubstanceStateEdition.show()
        self.ui.EditNameSubstance.show()
        self.ui.CancleEditionSubstance.show()
        self.ui.idsubstance.show()
        
        self.hiddenInfo()
        
        self.ui.EditionSubstanceHF.show()
        self.ui.EditionSubstanceSF.show()
        self.ui.EditionSubstanceGF.show()
        self.ui.newFomula.show()
        self.ui.Formula.show()
    
    def cancleEdition(self):
        self.ui.EditionSubstanceHF.clear()
        self.ui.EditionSubstanceSF.clear()
        self.ui.EditionSubstanceGF.clear()
        self.hiddenEdition()
    
    def hiddenEdition(self):
        self.ui.SaveEditionSubstance.hide()
        self.ui.SubstanceStateEdition.hide()
        self.ui.EditNameSubstance.hide()
        self.ui.NameFormulSubstance.show()
        self.ui.backFindDB.show()
        self.ui.CancleEditionSubstance.hide()
        self.ui.idsubstance.hide()
        self.ui.EditionSubstanceHF.hide()
        self.ui.EditionSubstanceSF.hide()
        self.ui.EditionSubstanceGF.hide()
        self.ui.newFomula.hide()
        self.ui.Formula.hide()
        self.ui.SubstanceHF.show()
        self.ui.SubstanceSF.show()
        self.ui.SubstanceGF.show()
        self.ui.EditionSubstance.show()
    
    def hiddenInfo(self):
        self.ui.SubstanceHF.hide()
        self.ui.SubstanceSF.hide()
        self.ui.SubstanceGF.hide()
        self.ui.NameFormulSubstance.hide()
        self.ui.backFindDB.hide()
        self.ui.EditionSubstance.hide()
            
    def saveEditionSubstance(self):
        substance = Substance(uid=self.ui.idsubstance.text())
        EditionName = self.ui.EditNameSubstance.text()
        EditionH_F = self.ui.EditionSubstanceHF.text()
        EditionS_F = self.ui.EditionSubstanceSF.text()
        EditionG_F = self.ui.EditionSubstanceGF.text()
        EditionFormula = self.ui.newFomula.text()
        EditionState = '({})'.format(
            self.ui.SubstanceStateEdition.currentText()[0].lower())
        substance.editionSubstanced(newname=EditionName, newHF=EditionH_F,
                          newSF=EditionS_F, newGF=EditionG_F, newState=EditionState,
                                      newFormula=EditionFormula)
        

        self.hiddenEdition()
        self.showInfoSubstance(substance.id)
    
    def NewSubstenced(self):
        self.ui.FindSubstancesDb.hide()
        self.ui.NewSubstenced.show()
        self.ui.Result.hide()
        
    def closeNewSubstenced(self):
        self.ui.NewSubstenced.hide()
        self.ui.FindSubstancesDb.show()
  
    def createNewSubstenced(self):
        substanced = Substance(new=True)
        name = self.ui.NewNameSubstance.text()
        formula = self.ui.newFomulaSubstanced.text()
        state = '({})'.format(
            self.ui.NewSubstanceState.currentText()[0].lower())
        HF = self.ui.NewSubstanceHF.text()
        SF = self.ui.NewSubstanceSF.text()
        GF = self.ui.NewSubstanceGF.text()
        Cp = self.ui.NewSubstanceCp.text()
        substanced.addSubstanced()
        substanced.editionSubstanced(newname=name, newHF=HF, newCp=Cp,
                            newSF=SF, newGF=GF, newState=state, newFormula=formula)
        
        self.ui.Result.show()
  
app = QtWidgets.QApplication([])
application = mobile()
application.show()

sys.exit(app.exec())
