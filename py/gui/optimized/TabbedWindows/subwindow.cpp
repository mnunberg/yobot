#include "subwindow.h"
#include <QVBoxLayout>
#include <QKeyEvent>
#include "twutil.h"
SubWindow::SubWindow(QWidget *parent, QString title) :
    QMainWindow(parent)
{
    this->title = title;
	setAttribute(Qt::WA_DeleteOnClose);
	setObjectName("subwindow");
	twutil->logCreation(this);
	connect(this, SIGNAL(destroyed()), twutil, SLOT(dumpDestroyed()));
}

void SubWindow::init(TabContainer *tc)
{
    this->tabcontainer = 0;
    if(!tc) {
        tc = TabContainer::getContainer();
        if(!tc) {
			twlog_warn("tc is still null");
            tc = new TabContainer(parentWidget());
            TabContainer::addContainer(tc);
        }
    }
    /*by all accounts, tc should not be NULL if things are working right*/
    if(!tc) {
		twlog_crit("%s: %s: tc is still NULL!", __FILE__, __func__);
        return;
    }
    addToContainer(tc);
    /*this->tabcontainer is set by that method as well*/

}


void SubWindow::addToContainer(TabContainer *tc)
{
    setWindowFlags(Qt::Widget);
    if(this->tabcontainer)
        removeFromContainer();
    this->tabcontainer = tc;
    tc->realTabWidget->addTab(this, this->title);
}
void SubWindow::removeFromContainer()
{
    if (this->tabcontainer) {
        int index = tabcontainer->realTabWidget->indexOf(this);
        if (index == -1)
            return;
        tabcontainer->realTabWidget->removeTab(index);
        this->tabcontainer = 0;
    }
}
void SubWindow::keyPressEvent(QKeyEvent *event)
{
    if (!(
          Qt::Key_1 <= event->key()
          && Qt::Key_9 <= event->key()
          && event->modifiers() & Qt::AltModifier
          && this->tabcontainer))
    {
        return;
    }
    tabcontainer->realTabWidget->setCurrentIndex(
            abs(Qt::Key_0 - event->key())-1);
}
void SubWindow::activateWindow()
{
    QMainWindow::activateWindow();
    raise();
    if (tabcontainer) {
        tabcontainer->activateWindow();
        tabcontainer->raise();
    }
}
