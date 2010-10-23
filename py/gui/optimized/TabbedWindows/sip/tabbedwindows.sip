%Module TabbedWindows 0
%Import QtGui/QtGuimod.sip
class SubWindow : QMainWindow
{
%TypeHeaderCode
#include "subwindow.h"
%End

public:
	SubWindow(QWidget *parent, QString title);
	TabContainer *tabcontainer;
	void removeFromContainer();
	void addToContainer(TabContainer*);
	QString title;
	void init(TabContainer*);
};

class TabContainer : QMainWindow {
%TypeHeaderCode
#include "tabcontainer.h"
%End

public:
	TabContainer(QWidget *parent=0);
	static TabContainer* getContainer();
	static void removeContainer(TabContainer*);

};
