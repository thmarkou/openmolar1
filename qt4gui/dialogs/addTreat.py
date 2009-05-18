# -*- coding: utf-8 -*-
# Copyright (c) 2009 Neil Wallace. All rights reserved.
# This program or module is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version. See the GNU General Public License for more details.

from __future__ import division

from PyQt4 import QtGui, QtCore
from openmolar.qt4gui.dialogs import Ui_addTreatment,Ui_treatmentItemWidget
from openmolar.settings import localsettings,fee_keys


def getCode(arg):
    '''converts a usercode into a computer code eg CE -> 101'''
    itemcode=4001
    try:
        itemcode=fee_keys.getKeyCode(arg)
    except:
        print "no itemcode found for item %s - will revert to OTHER TREATMENT"%arg
    return itemcode

def getFee(cset,numberOfItems,itemcode):
    feePerItem=0
    if "P" in cset:
        try:
            return localsettings.privateFees[itemcode].getFee(numberOfItems)
        except:
            print "no fee found for item %s"%itemcode
    return numberOfItems*feePerItem

def getDescription(arg):
    description=""
    try:
        description=localsettings.descriptions[arg]
    except:
        print "no description found for item %s"%arg
    return description

class itemWidget(Ui_treatmentItemWidget.Ui_Form):
    def __init__(self,parent,widget):
        self.parent=parent
        self.setupUi(widget)
        QtCore.QObject.connect(self.spinBox,
                               QtCore.SIGNAL("valueChanged(int)"), self.feeCalc)
        #self.itemfee=0

    def setNumber(self,arg):
        self.spinBox.setValue(arg)

    def setItem(self,itemcode):
        self.itemcode=itemcode
        self.description=getDescription(self.itemcode)
        self.label.setText(self.description+"\t(%s)"%self.itemcode)

    def feeCalc(self,arg):
        fee=getFee(self.parent.cset,arg,self.itemcode) / 100
        self.doubleSpinBox.setValue(fee)
        self.parent.updateTotal()

class treatment(Ui_addTreatment.Ui_Dialog):
    def __init__(self,dialog,items,cset):
        self.setupUi(dialog)
        self.dialog=dialog
        self.items=[]
        for item in items:
            self.items.append((item[0],getCode(item[1]),item[1]),)
        self.cset=cset
        self.showItems()

    def showItems(self):
        self.itemWidgets=[]
        vlayout = QtGui.QVBoxLayout(self.frame)
        for item in self.items:
            iw=QtGui.QWidget()
            i=itemWidget(self,iw)
            i.setItem(item[1])
            i.setNumber(item[0])
            i.usercode=item[2]
            self.itemWidgets.append(i)
            vlayout.addWidget(iw)

    def updateTotal(self):
        total=0
        for widg in self.itemWidgets:
            total+=widg.doubleSpinBox.value()

        self.fee_doubleSpinBox.setValue(total)

    def getInput(self):
        if self.dialog.exec_():
            retarg=()
            for i in self.itemWidgets:
                number=i.spinBox.value()
                fee=int(i.doubleSpinBox.value()*100)
                if number>0:
                    retarg+=((number,i.itemcode,i.usercode,i.description, fee),)
            return retarg
        else:
            return()

if __name__ == "__main__":
    import sys
    localsettings.initiate()
    app = QtGui.QApplication(sys.argv)
    Dialog = QtGui.QDialog()
    items=[(0,"CE"),(0,"M"),(1,"SP")]
    for i in range(2):
        items.append((0,"ECE"),)
    ui = treatment(Dialog,items,"P")
    print ui.getInput()

