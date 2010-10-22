#include "tabcontainer.h"
#include "_tabbar.h"
#include <QDragEnterEvent>
#include <QDropEvent>
#include <QCloseEvent>
#include <QMimeData>
#include <QMenuBar>
#include <QPointer>

/*initialize static members*/
QSet<TabContainer*> TabContainer::refs = QSet<TabContainer*>();

TabContainer::TabContainer(QWidget *parent) :
    QMainWindow(parent)
{
    qDebug("%s:%s [%p]", __FILE__, __func__, this);
    setWindowFlags(Qt::Window);
    setAcceptDrops(true);
	setAttribute(Qt::WA_DeleteOnClose);
    realTabWidget = new RealTabWidget(this);
    connect(realTabWidget, SIGNAL(tabCloseRequested(int)), this,
            SLOT(rtwTabCloseRequested(int)));
    connect(realTabWidget, SIGNAL(currentChanged(int)), this,
            SLOT(rtwCurrentChanged(int)));
    connect(realTabWidget, SIGNAL(SIG_tabRemoved(int)), this,
            SLOT(rtwSIG_TabRemoved(int)));
    setCentralWidget(realTabWidget);
    show();
    qDebug("done");
}

void TabContainer::rtwSIG_TabRemoved(int)
{
    realTabWidget->count() || close();
}

void TabContainer::dragEnterEvent(QDragEnterEvent *event)
{
    if (event->mimeData()->data("action") == QString("window_drag"))
        event->acceptProposedAction();
}

void TabContainer::dropEvent(QDropEvent *event)
{
    const QMimeData *mimedata = event->mimeData();
    _TabBar *src = qobject_cast<_TabBar*>(event->source());
    if (src &&
        mimedata->hasFormat("action") &&
        mimedata->data("action") == "window_drag") {
        event->acceptProposedAction();
        QWidget *widget = src->currentWidget();
        if(!widget) {
            qDebug("Got bad object");
            return;
        }
        if(realTabWidget->tabIds.contains(widget)) {
            qDebug("Requested to add %p which already exists",
                   widget);
            return;
        }
        SubWindow *sw = qobject_cast<SubWindow*>(widget);
        if(!sw) {
			qWarning("Failed to cast to subwindow");
            return;
        }
        sw->addToContainer(this);
    }
}

void TabContainer::rtwTabCloseRequested(int index)
{
    QWidget *widget = realTabWidget->widget(index);
    realTabWidget->removeTab(index);
    widget->close();
//    widget->deleteLater();
}
void TabContainer::rtwCurrentChanged(int)
{
    /*restore ownership to existing menubar*/
    QWidget *oldmenubar = menuWidget();
    if(oldmenubar) {
        QPointer<QMainWindow> owner = menuOwners.value(oldmenubar);
        if(!owner.isNull()) {
            owner.data()->setMenuWidget(menuBar());
        } else {
            qDebug("Deleting stale pointer..");
            menuOwners.remove(oldmenubar);
			oldmenubar->deleteLater();
            setMenuWidget(0);
        }
    } else {
        qDebug("%s: old menubar is NULL", __func__);
    }
    QMainWindow *mw = qobject_cast<QMainWindow*>(realTabWidget->currentWidget());
    if (!mw) {
        qDebug("%s: mw is null", __func__);
        return;
    }
    QWidget *menubar = mw->menuWidget();
    if (menubar) {
        menuOwners.insert(menubar, QPointer<QMainWindow>(mw));
    }
    setMenuWidget(menubar);
}


void TabContainer::closeEvent(QCloseEvent *event)
{
	qDebug("%s: closing.. %p", __func__, this);
	qDebug("%s: parent is %p", __func__, parentWidget());
    event->accept();
    refs.remove(this);
}

TabContainer* TabContainer::getContainer()
{
    QSet<TabContainer*>::iterator i;
    for(i=refs.begin();i!=refs.end(); i++) {
        if((*i)->isActiveWindow()) {
            return *i;
        }
    }
    return *i;
}
void TabContainer::addContainer(TabContainer *tc)
{
    refs.insert(tc);
}
void TabContainer::removeContainer(TabContainer *tc)
{
    refs.remove(tc);
}
