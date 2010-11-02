#!/usr/bin/env python

from PyQt4.QtGui import (QComboBox, QMainWindow, QStandardItemModel, QStandardItem,
                         QIcon, QPixmap, QImage, QPainter, QDialog, QMessageBox,
                         QApplication, QFont, QTextEdit, QColorDialog, QPalette,
                         QListWidget, QListWidgetItem, QStyledItemDelegate,
                         QStyleOptionViewItem, QRegion, QWidget, QBrush, QStyle,
                         QPen, QPushButton, QStyleOption, QMenu, QAction, QCursor,
                         QTreeView, QLineEdit, QButtonGroup, QTabWidget, QApplication,
                         QVBoxLayout, QDialogButtonBox, QColor,
                         QTreeWidgetItem,
                         QErrorMessage, QFontDialog)

from PyQt4.QtCore import (QPoint, QSize, QModelIndex, Qt, QObject, SIGNAL, QVariant,
                          QAbstractItemModel, QRect, QRectF, QPointF, QObject)

import sys
sys.path.append("../")

signal_connect = QObject.connect
import yobotproto
import _config_dialog
import _account_settings
from gui_util import getIcon, proto_name_int, mkProtocolComboBox, widgetformatter, getProtoIconAndName
from debuglog import log_debug, log_err, log_warn, log_crit, log_info



import yobot_interfaces
import yobotops

ITEM_PLACEHOLDER_ROLE = Qt.UserRole + 1

class AccountSettingsDialog(QDialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        w = _account_settings.Ui_Dialog()
        w.setupUi(self)
        self.widgets = w
        self.settings_dict = {}
        
        signal_connect(w.use_proxy, SIGNAL("toggled(bool)"), self.widgets.proxy_params.setEnabled)
        mkProtocolComboBox(w.improto)
        self.values = {}
        self.setWindowTitle("Configure Account")
        
    def fill_from(self, account_dict):
        w = self.widgets
        w.username.setText(account_dict.get("name", ""))
        w.password.setText(account_dict.get("password", ""))
        
        #get protocol constant
        improto_constant = getattr(yobotproto, str(account_dict.get("improto")))
        log_debug("improto_constant", improto_constant)
        #find it in the combobox
        i = w.improto.findData(QVariant(improto_constant))
        if i >= 0:
            w.improto.setCurrentIndex(i)
        else:
            log_warn("couldn't find improto_constant", improto_constant)
        if account_dict.get("use_proxy", False) and account_dict.get("proxy_params", False):
            w.use_proxy.setChecked(True)
            pp = account_dict["proxy_params"]
            
            proxy_type_index = w.improto.findText(pp.get("proxy_type", "").upper())
            if proxy_type_index >= 0:
                w.proxy_type.setCurrentIndex(proxy_type_index)
            w.proxy_address.setText(pp.get("proxy_address"))
            w.proxy_port.setText(pp.get("proxy_port"))
            w.proxy_username.setText(pp.get("proxy_username", ""))
            w.proxy_password.setText(pp.get("proxy_password", ""))
        else:
            w.use_proxy.setChecked(False)
            
    def accept(self):
        #validate input..
        #load the variables first..
        w = self.widgets
        name, password = w.username.text(), w.password.text()
        improto = yobotops.imprototostr(w.improto.itemData(w.improto.currentIndex()).toPyObject())
        log_debug("improto is", improto)
        
        use_proxy = w.use_proxy.isChecked()
        proxy_username, proxy_password, proxy_address, proxy_port = (
            w.proxy_username.text(), w.proxy_password.text(), w.proxy_address.text(), w.proxy_port.text())
        proxy_type = w.proxy_type.currentText()
        autoconnect = w.autoconnect.isChecked()
        
        err = False
        while not err:
            if not name or not password:
                err = "username and password required"
                break
            if use_proxy:
                if not proxy_address or not proxy_port:
                    err = "proxy requested but no port:address specified"
                    break
                if (proxy_password and not proxy_username) or (
                    proxy_username and not proxy_password):
                    err = "username and password must be specified together"
                    break
            break
        if err:
            QErrorMessage(self).showMessage(err)
            return
            
        a = {
            "name":str(name),
            "password":str(password),
            "improto":str(improto),
            "autoconnect":bool(autoconnect),
            "use_proxy":bool(use_proxy),
            "proxy_params": {
                "proxy_type":str(proxy_type),
                "proxy_address":str(proxy_address),
                "proxy_port":str(proxy_port),
                "proxy_username":str(proxy_username),
                "proxy_password":str(proxy_password),
            }
        }
        QDialog.accept(self)
        self.values = a
            

class ConfigDialog(QDialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self._layout = QVBoxLayout(self)
        self._tabdialog = QTabWidget(self)
        self._layout.addWidget(self._tabdialog)
        w = _config_dialog.Ui_config_dialog()
        w.setupUi(self._tabdialog)
        self.widgets = w
        
        self._buttonbox = QDialogButtonBox(QDialogButtonBox.Save|QDialogButtonBox.Cancel)
        self._buttonbox.setParent(self)
        signal_connect(self._buttonbox, SIGNAL("accepted()"), self.accept)
        signal_connect(self._buttonbox, SIGNAL("rejected()"), self.reject)
        self._layout.addWidget(self._buttonbox)
        
        self._layout.setContentsMargins(3,3,3,3)
        
        self.font = QFont()
        self.color = QColor()
        
        self.config = yobot_interfaces.component_registry.get_component("client-config")
        
        self.account_items = {}
        
        signal_connect(w.account_add, SIGNAL("clicked()"), lambda: self.add_modify_account(add=True))
        signal_connect(w.account_edit, SIGNAL("clicked()"), lambda: self.add_modify_account(add=False))
        signal_connect(w.account_del, SIGNAL("clicked()"), self.remove_account)
        
        signal_connect(w.select_color, SIGNAL("clicked()"), lambda: self.change_formatting(color=True))
        signal_connect(w.select_font, SIGNAL("clicked()"), lambda: self.change_formatting(font=True))
        
        signal_connect(w.agent_address, SIGNAL("editingFinished()"), self.change_agent)
        self.connect_global_bool(w.html_relsize, "appearance", "use_html_relsize")
        self.connect_global_bool(w.show_joinpart, "appearance", "show_joinpart")
        self.input_validated = True
        
        self.setWindowTitle("Yobot Configuration")
        
    def connect_global_bool(self, widget, dictname, optname, default=False):
        signal_connect(widget, SIGNAL("toggled(bool)"),
                       lambda b: self.config.globals.setdefault(dictname, {}).__setitem__(optname, b))
        
    def load_settings(self):
        w = self.widgets
        if not self.config:
            log_warn("config object not available! bailing")
            return
        #for font..
        appearance = self.config.globals.setdefault("appearance", {})
        family = appearance.get("font_family", None)
        size = appearance.get("font_size", None)
        color = appearance.get("font_color", None)
        
        if family: self.font.setFamily(family)
        if size: self.font.setPointSize(size)
        if color: self.color.setNamedColor(color)
        
        bold = appearance.get("font_bold", False)
        italic = appearance.get("font_italic", False)
        underline = appearance.get("font_underline", False)
        html_relsize = appearance.get("use_html_relsize", False)
        show_joinpart = appearance.get("show_joinpart", False)
        
        self.font.setBold(bold)
        self.font.setItalic(italic)
        self.font.setUnderline(underline)
        w.html_relsize.setChecked(html_relsize)
        w.show_joinpart.setChecked(show_joinpart)
        
        self.change_formatting()
        
        #for the agent...
        agent = self.config.globals.get("agent_address", None)
        if agent: w.agent_address.setText(agent)
        self.change_agent()
        #for accounts:
        for a in self.config.accounts:
            log_warn("got account", a)
            if a.get("name", None) and a.get("improto", None):
                #get name and icon
                name, icon = getProtoIconAndName(getattr(yobotproto, a["improto"], ""))
                log_debug(icon, name)
                i = QTreeWidgetItem((a["name"], name))
                i.setIcon(1, icon)
                i.setData(0, ITEM_PLACEHOLDER_ROLE, a)
                self.account_items[i] = a
                self.widgets.accounts.addTopLevelItem(i)
                
    
    def remove_account(self):
        #get current item:
        w = self.widgets
        item = w.accounts.currentItem()
        
        #get the index (ugh.. this is tedious)
        itemindex = w.accounts.indexOfTopLevelItem(item)
        if itemindex == -1:
            log_err("couldn't get index!")
            return
        
        account = self.account_items[item]
        #remove the item from the widget:
        w.accounts.takeTopLevelItem(itemindex)
        
        #find the account in our global config list
        index = -1
        for i in xrange(0, len(self.config.accounts)):
            a = self.config.accounts[i]
            if str(a["name"]) == str(account["name"]) and str(a["improto"]) == str(account["improto"]):
                index = i
                break
            else:
                pass
        if index >= 0:
            log_debug("index:", index)
            self.config.accounts.pop(index)
        #finally, remove it from the mapping
        self.account_items.pop(item)
    
    def add_modify_account(self, add=False):
        dlg = AccountSettingsDialog(self)
        if not add:
            item = self.widgets.accounts.currentItem()
            if not item:
                return
            account = self.account_items.get(item)
            if not account:
                return
            #account = item.data(0, ITEM_PLACEHOLDER_ROLE).toPyObject()
            dlg.fill_from(account)
        else:
            item = QTreeWidgetItem()
        result = dlg.exec_()
        
        if not result == QDialog.Accepted:
            return
        new_a = dlg.values
        
        item.setText(0, new_a["name"])
        #get icon and name...
        name, icon = getProtoIconAndName(getattr(yobotproto, new_a["improto"], -1))
        item.setText(1, name)
        item.setIcon(1, icon)
        if add:
            if self.account_exists(new_a):
                print "account already exists.. not adding"
                return
            item.setData(0, ITEM_PLACEHOLDER_ROLE, new_a)
            self.widgets.accounts.addTopLevelItem(item)
            self.config.accounts.append(new_a)
        else:
            account.update(new_a)
            
    def account_exists(self, d):
        for a in self.config.accounts:
            if d["name"] == a["name"] and d["improto"] == a["improto"]:
                return True
        return False
    
    def change_formatting(self, color=False, font=False):
        if color:
            _color = QColorDialog.getColor(self.color, self, "Select Color")
            if _color.isValid():
                self.color = _color
        elif font:
            self.font, _ = QFontDialog.getFont(self.font, self, "Select Font")
            
        widgetformatter(self.widgets.sample_text, self.font, self.color,
                        klass="QPlainTextEdit")
        
        #now, change the config objects..
        fmt = self.config.globals["appearance"]
        fmt.update({
            "font_family":str(self.font.family()),
            "font_size":int(self.font.pointSize()),
            "font_color":str(self.color.name()),
            "font_bold":bool(self.font.bold()),
            "font_italic":bool(self.font.italic()),
            "font_underline":bool(self.font.underline())
        })
    
    def change_agent(self):
        #bah.. the same boring thing as always
        s = str(self.widgets.agent_address.text())
        if len(s.rsplit(":", 1)) == 2 and not str.isdigit(s.rsplit(":",1)[1]):
            self.input_validated = False
            self.widgets.agent_address.setStyleSheet("background-color:red;")
        else:
            self.widgets.agent_address.setStyleSheet("background-color:green")
            if s:
                self.config.globals["agent_address"] = str(s)
            self.input_validated = True
            
            
    
    def accept(self):
        #do some stuff first, like save
        if self.input_validated:
            self.config.save()
            QDialog.accept(self)
        else:
            QErrorMessage(self).showMessage("Bad input.. (somewhere?)")
    
if __name__ == "__main__":
    import sys
    import client_config
    import simplejson
    import debuglog
    debuglog.init("config_dialog", "cyan")
    app = QApplication(sys.argv)
    
    config = client_config.ClientConfig("/tmp/yobot_client_config", autocreate=True)
    yobot_interfaces.component_registry.register_component("client-config", config)
    
    #create some more account objects..
    a0 = {"name":"user0",
          "password":"pass0",
          "improto":"YOBOT_AIM",
          "autoconnect":True}
    a1 = a0.copy()
    a1["name"] = "user1"
    
    config.accounts.append(a0)
    config.accounts.append(a1)
    
    config.save()
    
    dlg = ConfigDialog()
    dlg.load_settings()
    dlg.show()
    app.exec_()
