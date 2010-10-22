#include "tabcontainer.h"
#include "_tabbar.h"
#include <QDragEnterEvent>
#include <QDropEvent>
#include <QCloseEvent>
#include <QMimeData>
#include <QMenuBar>
#include <QPointer>
#include "twutil.h"

#define fn_begin qDebug("[%p] %s: BEGIN", this, __PRETTY_FUNCTION__);
#define fn_end qDebug("[%p] %s: END", this, __PRETTY_FUNCTION__);

/*initialize static members*/
QSet<TabContainer*> TabContainer::refs = QSet<TabContainer*>();

TabContainer::TabContainer(QWidget *parent) :
    QMainWindow(parent)
{
	setObjectName("tabcontainer");
	twutil->logCreation(this);
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
	connect(this, SIGNAL(destroyed()), twutil, SLOT(dumpDestroyed()));
	_TabBar *tb = qobject_cast<_TabBar*>(realTabWidget->tabBar());
	Q_ASSERT(tb);
	connect(tb, SIGNAL(widgetDnD(QWidget*,QWidget*)), this,
			SLOT(handleDnD(QWidget*,QWidget*)), Qt::QueuedConnection);

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
	fn_begin;
	const QMimeData *mimedata = event->mimeData();
    _TabBar *src = qobject_cast<_TabBar*>(event->source());
	if (src && mimedata &&
        mimedata->hasFormat("action") &&
        mimedata->data("action") == "window_drag") {
        event->acceptProposedAction();
        QWidget *widget = src->currentWidget();
        if(!widget) {
            qDebug("Got bad object");
			goto ret;
        }
        if(realTabWidget->tabIds.contains(widget)) {
			qDebug("Requested to add %p which already exists in %p",
				   widget, this);
			goto ret;
        }
        SubWindow *sw = qobject_cast<SubWindow*>(widget);
        if(!sw) {
			qWarning("Failed to cast to subwindow");
			goto ret;
        }
        sw->addToContainer(this);
    }
	ret:
	fn_end;
}

void TabContainer::handleDnD(QWidget* source, QWidget* target)
{
	TabContainer *tc = qobject_cast<TabContainer*>(target);
	if(!tc) {
		disconnect(this, SLOT(rtwSIG_TabRemoved(int)));
		qDebug("%s: did not get a valid target %p, detaching",
			   __PRETTY_FUNCTION__, source);
		SubWindow *sw = qobject_cast<SubWindow*>(source);
		if(!sw) {
			qWarning("%s: Expected SubWindow instance!", __PRETTY_FUNCTION__);
			goto cleanup;
		}
		Q_ASSERT(realTabWidget->tabIds.contains(source));

		/*re-use old pointer*/
		tc = new TabContainer(parentWidget());
		sw->addToContainer(tc);
		tc->show();
		tc->resize(size());
		tc->move(QCursor().pos());
	} else {
		qDebug("%s [this %p] dropped on TabContainer %p",
			   __PRETTY_FUNCTION__, this, tc);
	}
	cleanup:
	if (realTabWidget->count()) {
		connect(realTabWidget, SIGNAL(SIG_tabRemoved(int)), this, SLOT(rtwSIG_TabRemoved(int)));
	} else {
		if(!realTabWidget->count()) {
			qDebug("%s: Deleting objects...", __PRETTY_FUNCTION__);
			realTabWidget->setParent(0);
			connect(this, SIGNAL(destroyed()), realTabWidget, SLOT(deleteLater()));
			deleteLater();
		}
	}
	return;
}

void TabContainer::rtwTabCloseRequested(int index)
{
    QWidget *widget = realTabWidget->widget(index);
    realTabWidget->removeTab(index);
    widget->close();
	widget->deleteLater();
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
		qDebug("%s: old menubar is NULL", __PRETTY_FUNCTION__);
    }
    QMainWindow *mw = qobject_cast<QMainWindow*>(realTabWidget->currentWidget());
    if (!mw) {
		qDebug("%s: mw is null", __PRETTY_FUNCTION__);
		fn_end
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
	fn_begin;
	qDebug("%s: closing.. %p", __PRETTY_FUNCTION__, this);
	qDebug("%s: parent is %p", __PRETTY_FUNCTION__, parentWidget());
    event->accept();
    refs.remove(this);
	if (event->spontaneous()) {
		deleteLater();
	}
	fn_end;
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
