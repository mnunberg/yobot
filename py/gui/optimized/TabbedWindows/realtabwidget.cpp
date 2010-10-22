#include "realtabwidget.h"
#include "_tabbar.h"
#include "twutil.h"
RealTabWidget::RealTabWidget(QWidget *parent) :
    QTabWidget(parent)
{
	setObjectName("realtabwidget");
	connect(this, SIGNAL(destroyed()), twutil, SLOT(dumpDestroyed()));
    setTabBar(new _TabBar(this));
    setTabsClosable(true);
    tabBar()->setExpanding(true);
}
void RealTabWidget::addTab(QWidget *widget, QString title)
{
    tabIds.insert(widget);
    QTabWidget::addTab(widget, title);
    setCurrentWidget(widget);
}
void RealTabWidget::removeTab(int index)
{
//	qDebug("%s: removing %p", __PRETTY_FUNCTION__, widget(index));
    tabIds.remove(widget(index));
    QTabWidget::removeTab(index);
}
void RealTabWidget::tabRemoved(int index)
{
    emit SIG_tabRemoved(index);
}
void RealTabWidget::tabInserted(int index)
{
    emit SIG_tabInserted(index);
}
