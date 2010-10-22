#include "realtabwidget.h"
#include "_tabbar.h"
RealTabWidget::RealTabWidget(QWidget *parent) :
    QTabWidget(parent)
{
    setTabBar(new _TabBar(this));
    setTabsClosable(true);
    tabBar()->setExpanding(true);
}
void RealTabWidget::addTab(QWidget *widget, QString title)
{
    tabIds.insert(widget);
    QTabWidget::addTab(widget, title);
    setCurrentWidget(widget);

    qDebug("%s:done", __func__);
}
void RealTabWidget::removeTab(int index)
{
    qDebug("%s: deleting %p", __func__, widget(index));
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
