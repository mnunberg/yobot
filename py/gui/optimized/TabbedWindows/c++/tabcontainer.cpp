#include "tabcontainer.h"
#include "tabbar.h"
#include <QDragEnterEvent>
#include <QDropEvent>
#include <QCloseEvent>
#include <QMimeData>
#include <QMenuBar>
#include <QPointer>
#include "twutil.h"


/*initialize static members*/
QSet<TabContainer*> TabContainer::refs = QSet<TabContainer*>();

TabContainer::TabContainer(QWidget *parent) :
    QMainWindow(parent)
{
	setObjectName("tabcontainer");
	twutil->logCreation(this);
    setWindowFlags(Qt::Window);
    setAcceptDrops(true);
    realTabWidget = new RealTabWidget(this);
    connect(realTabWidget, SIGNAL(tabCloseRequested(int)), this,
            SLOT(rtwTabCloseRequested(int)));
    connect(realTabWidget, SIGNAL(currentChanged(int)), this,
            SLOT(rtwCurrentChanged(int)));
    connect(realTabWidget, SIGNAL(SIG_tabRemoved(int)), this,
            SLOT(rtwSIG_TabRemoved(int)));
	connect(this, SIGNAL(destroyed()), twutil, SLOT(dumpDestroyed()));
	TabBar *tb = qobject_cast<TabBar*>(realTabWidget->tabBar());
	Q_ASSERT(tb);
	connect(tb, SIGNAL(widgetDnD(QWidget*,QWidget*)), this,
			SLOT(handleDnD(QWidget*,QWidget*)), Qt::QueuedConnection);

    setCentralWidget(realTabWidget);
	deleteRequested = false;
    show();
}

void TabContainer::rtwSIG_TabRemoved(int)
{
    realTabWidget->count() || close();
}

void TabContainer::dragEnterEvent(QDragEnterEvent *event)
{
	twlog_debug("");
    if (event->mimeData()->data("action") == QString("window_drag"))
        event->acceptProposedAction();
}

void TabContainer::dropEvent(QDropEvent *event)
{
	fn_begin;
	const QMimeData *mimedata = event->mimeData();
    TabBar *src = qobject_cast<TabBar*>(event->source());
	if (src && mimedata &&
        mimedata->hasFormat("action") &&
        mimedata->data("action") == "window_drag") {
        event->acceptProposedAction();
        QWidget *widget = src->currentWidget();
        if(!widget) {
			twlog_warn("Got bad object");
			goto ret;
        }
        if(realTabWidget->tabIds.contains(widget)) {
			twlog_debug("Requested to add %p which already exists", widget);
			goto ret;
        }
        SubWindow *sw = qobject_cast<SubWindow*>(widget);
        if(!sw) {
			twlog_crit("Failed to cast to subwindow");
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
	if(!tc && realTabWidget->count() != 1) {
		/*Not a valid target and this is not the only tab.. detach window*/
		disconnect(this, SLOT(rtwSIG_TabRemoved(int)));
		twlog_debug("did not get a valid target %p, detaching", source);
		SubWindow *sw = qobject_cast<SubWindow*>(source);
		if(!sw) {
			twlog_warn("Expected SubWindow instance!");
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
		twlog_debug("dropped on TabContainer %p", tc);
	}
	cleanup:
	if (realTabWidget->count()) {
		connect(realTabWidget, SIGNAL(SIG_tabRemoved(int)), this, SLOT(rtwSIG_TabRemoved(int)));
	} else {
		if(!realTabWidget->count()) {
			twlog_debug("deleting objects");
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
	if (!realTabWidget->count()) {
		deleteLater();
	}
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
			twlog_debug("deleting stale pointer");
            menuOwners.remove(oldmenubar);
			deleteRequested = true;
			oldmenubar->deleteLater();
            setMenuWidget(0);
        }
    } else {
		twlog_debug("old menubar is NULL");
    }
    QMainWindow *mw = qobject_cast<QMainWindow*>(realTabWidget->currentWidget());
    if (!mw) {
		twlog_debug("mw is NULL");
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
	twlog_debug("closing, parent is %p", parentWidget());
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
