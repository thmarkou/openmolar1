#! /usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
##                                                                           ##
##  Copyright 2010, Neil Wallace <rowinggolfer@googlemail.com>               ##
##                                                                           ##
##  This program is free software: you can redistribute it and/or modify     ##
##  it under the terms of the GNU General Public License as published by     ##
##  the Free Software Foundation, either version 3 of the License, or        ##
##  (at your option) any later version.                                      ##
##                                                                           ##
##  This program is distributed in the hope that it will be useful,          ##
##  but WITHOUT ANY WARRANTY; without even the implied warranty of           ##
##  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the            ##
##  GNU General Public License for more details.                             ##
##                                                                           ##
##  You should have received a copy of the GNU General Public License        ##
##  along with this program.  If not, see <http://www.gnu.org/licenses/>.    ##
##                                                                           ##
###############################################################################

from PyQt4 import QtCore, QtGui

class CurrencyLabel(QtGui.QWidget):
    '''
    a re-implimentation of QLabel which adds the local currency prefix 
    if possible.
    '''
    def __init__(self, text="", parent=None):
        QtGui.QWidget.__init__(self, parent)
        try:
            c_txt = QtCore.QLocale().currencySymbol()
        except AttributeError:
            #currencySymbol is Qt 4.8 and above
            c_txt = ""
            
        self.suffix_label = QtGui.QLabel(c_txt, self)
        self.suffix_label.setFixedWidth(
            self.suffix_label.fontMetrics().width(c_txt))
        self.label = QtGui.QLabel(text,self)
        self.label.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter)
            
        self.text = self.label.text
        self.setText = self.label.setText
        
        layout = QtGui.QHBoxLayout(self)
        layout.addWidget(self.suffix_label)
        layout.addWidget(self.label)
    
    def setFont(self, font):
        self.label.setFont(font)
        self.suffix_label.setFont(font)
        

if __name__ == "__main__":

    app = QtGui.QApplication([])
    label = CurrencyLabel("hello")
    label.show()
    app.exec_()

