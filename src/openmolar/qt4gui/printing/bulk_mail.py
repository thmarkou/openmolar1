# -*- coding: utf-8 -*-
# Copyright (c) 2009 Neil Wallace. All rights reserved.
# This program or module is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version. See the GNU General Public License for more details.

import math
import sys
from PyQt4 import QtCore, QtGui

from openmolar.settings import localsettings

DATE_FORMAT = "MMMM, yyyy"

class omLetter(object):
    def __init__(self):
        self.salutation = ""
        self.patients = ""
        self.address = ""
        self.body = '''%s <<SALUTATION>>,\n%s\n\n%s\n\n%s\n\n%s'''%(
_("Dear"),
_("We are writing to inform you that your dental examination is now due."),
_("Please contact the surgery to arrange an appointment. *"),
_("We look forward to seeing you in the near future."),
_("Yours sincerely,"))
        self.signature = localsettings.CORRESPONDENCE_SIG

        self.footer = _('''* If you already have a future appointment with us -
please accept our apologies and ignore this letter.''')

class TreeItem(object):
    def __init__(self, data, parent=None):
        self.parentItem = parent
        self.itemData = data
        self.childItems = []

    def appendChild(self, item):
        self.childItems.append(item)

    def child(self, row):
        return self.childItems[row]

    def childCount(self):
        return len(self.childItems)

    def columnCount(self):
        return len(self.itemData)

    def data(self, column):
        try:
            return QtCore.QVariant(self.itemData[column])
        except IndexError:
            return None

    def parent(self):
        return self.parentItem

    def row(self):
        if self.parentItem:
            return self.parentItem.childItems.index(self)

        return 0

class treeModel(QtCore.QAbstractItemModel):
    def __init__(self, header, mydata):
        super(QtCore.QAbstractItemModel, self).__init__()
        self.rootItem = TreeItem(header)
        self.setupModelData(mydata, self.rootItem)

    def columnCount(self, parent):
        if parent.isValid():
            return parent.internalPointer().columnCount()
        else:
            return self.rootItem.columnCount()

    def data(self, index, role):
        if not index.isValid():
            return None

        if role != QtCore.Qt.DisplayRole:
            return None

        item = index.internalPointer()

        return item.data(index.column())

    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.NoItemFlags

        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def headerData(self, section, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self.rootItem.data(section)

        return None

    def index(self, row, column, parent):
        if not self.hasIndex(row, column, parent):
            return QtCore.QModelIndex()

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()

        childItem = parentItem.child(row)
        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QtCore.QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QtCore.QModelIndex()

        childItem = index.internalPointer()
        parentItem = childItem.parent()

        if parentItem == self.rootItem:
            return QtCore.QModelIndex()

        return self.createIndex(parentItem.row(), 0, parentItem)

    def rowCount(self, parent):
        if parent.column() > 0:
            return 0

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()

        return parentItem.childCount()

    def setupModelData(self, lines, parent):
        parents = [parent]
        indentations = [0]

        number = 0
        letterNo = 0
        
        for lineData in lines:
            position = 0
            
            if lineData[0] == letterNo:
                position = 1
            letterNo = lineData[0]
            
            if position > indentations[-1]:
                if parents[-1].childCount() > 0:
                    parents.append(parents[-1].child(parents[-1].childCount() - 1))
                    indentations.append(position)
            else:
                while position < indentations[-1] and len(parents) > 0:
                    parents.pop()
                    indentations.pop()

            parents[-1].appendChild(TreeItem(lineData, parents[-1]))


class bulkMails(object):
    def __init__(self, om_gui):
        self.om_gui = om_gui
        self.printer = QtGui.QPrinter()
        self.printer.setPageSize(QtGui.QPrinter.A5)
        self.headers = ()
        self.recipients = ()
        self.adate = localsettings.currentDay()

    def setData(self, headers, recipients):
        '''
        load the recipient data
        '''
        self.headers = headers
        self.recipients = recipients
        self.populateTree()
        
    def populateTree(self):
        '''
        load the bulk mailing tree view
        '''
        bulk_model = treeModel(self.headers, self.recipients)
        self.om_gui.ui.bulk_mailings_treeView.setModel(bulk_model)

    def iterate_letters(self):
        '''
        iterate over the letters
        '''
        letters = {}
        for recipient in self.recipients:
            if letters.has_key(recipient.letterno):
                letters[recipient.letterno].append(recipient)
            else:
                letters[recipient.letterno] = [recipient]

        for key in sorted(letters):
            recipients = letters[key]
            head = recipients[0]
            address = '%s\n%s\n%s\n%s\n%s\n%s'% (
            head.addr1.title(), head.addr2.title(), 
            head.addr3.title(), head.town, 
            head.county, head.pcde)
            
            letter = omLetter()
            while "\n\n" in address:
                address = address.replace("\n\n","\n")
            letter.address = address

            letter.names = ""
            for r in recipients:
                letter.names += "%s %s %s, "% (r.title, r.fname, r.sname)
            letter.names = letter.names.rstrip(", ")
            
            letter.salutation = "%s %s %s,"% (head.title, head.fname, 
            head.sname)
            
            for r in recipients[1:]:
                if r.age > 18:
                    letter.salutation += "\n%s %s %s"% (r.title, r.fname, 
                    r.sname)
                else:
                    letter.salutation += ", %s"% (r.fname)

            if ", " in letter.salutation:
                i = letter.salutation.rindex(", ")
                letter.salutation = "%s and%s"% (letter.salutation[:i],
                letter.salutation[i+1:])
                
            yield letter, key == sorted(letters)[-1]

    def printViaQPainter(self, showRects = False):
        dialog = QtGui.QPrintDialog(self.printer, self.om_gui)
        if not dialog.exec_():
            return
        
        sansFont = QtGui.QFont("Helvetica", 9)
        sansLineHeight = QtGui.QFontMetrics(sansFont).height()
        serifFont = QtGui.QFont("Times", 10)
        serifLineHeight = QtGui.QFontMetrics(serifFont).height()
        sigFont = QtGui.QFont("Lucida Handwriting",8)
        fm = QtGui.QFontMetrics(serifFont)
        datewidth = fm.width(" September 99, 2999 ")
        dateheight = fm.height()
        pageRect = self.printer.pageRect()
        
        LEFT = 50
        TOP = 120
        RECT_WIDTH = pageRect.width() - (2 * LEFT)
        ADDRESS_HEIGHT = 120
        FOOTER_HEIGHT = 120
        
        addressRect = QtCore.QRectF(LEFT, TOP, RECT_WIDTH, ADDRESS_HEIGHT)

        dateRect = QtCore.QRectF(RECT_WIDTH - datewidth, TOP + ADDRESS_HEIGHT,
        datewidth, dateheight)

        bodyRect = QtCore.QRectF(LEFT, TOP + ADDRESS_HEIGHT + dateheight,
        RECT_WIDTH, pageRect.height()/2)

        footerRect = QtCore.QRectF(LEFT, 
        pageRect.height() - TOP - FOOTER_HEIGHT, 
        RECT_WIDTH, FOOTER_HEIGHT)
        
        painter = QtGui.QPainter(self.printer)
        
        page = 1
        for letter, lastpage in self.iterate_letters():        
            painter.save()
            painter.setPen(QtCore.Qt.black)
            
            option = QtGui.QTextOption(QtCore.Qt.AlignLeft)
            option.setWrapMode(QtGui.QTextOption.WordWrap)
            
            ##address
            painter.drawText(addressRect, "%s\n%s"% (
            letter.salutation, letter.address), option)
            if showRects:
                painter.drawRect(addressRect)
            
            painter.drawText(dateRect, 
            localsettings.formatDate(self.adate))
            painter.setFont(serifFont)
            if showRects:
                painter.drawRect(dateRect)
            
            ##body
            painter.drawText(bodyRect, 
            letter.body.replace("<<SALUTATION>>",letter.salutation), option)

            painter.setFont(sigFont)
            font = QtGui.QFont("Helvetica", 7)
            font.setItalic(True)
            painter.setFont(font)            
            
            painter.drawText(bodyRect.adjusted(0,bodyRect.height()/2,0,0), 
            letter.signature, option)
            if showRects:
                painter.drawRect(bodyRect)
            
            ##footer
            painter.drawLine(footerRect.topLeft(), footerRect.topRight())
            font = QtGui.QFont("Helvetica", 7)
            font.setItalic(True)
            painter.setFont(font)
            
            option = QtGui.QTextOption(QtCore.Qt.AlignCenter)
            option.setWrapMode(QtGui.QTextOption.WordWrap)
            
            painter.drawText(footerRect, letter.footer, option) 
            if showRects:
                painter.drawRect(footerRect)
            
            page += 1
            if not lastpage:
                self.printer.newPage()
            painter.restore()

if __name__ == "__main__":
    
    app = QtGui.QApplication([])
    import datetime
    from openmolar.qt4gui import maingui
    from openmolar.dbtools import recall
    om_gui = maingui.openmolarGui(app)
    start = datetime.date(2009,2,1)
    end = datetime.date(2009,2,1)
    
    letters = bulkMails(om_gui)
    letters.setData(recall.HEADERS, recall.getpatients(start, end))
    letters.printViaQPainter(True)
    app.closeAllWindows()