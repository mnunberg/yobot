#ifndef _TABBAR_H
#define _TABBAR_H

#include <QTabBar>
#include "realtabwidget.h"
#include <QMouseEvent>
class _TabBar : public QTabBar
{
Q_OBJECT
public:
    explicit _TabBar(RealTabWidget*);
    void mousePressEvent(QMouseEvent *);
    void mouseMoveEvent(QMouseEvent *);
    QWidget *currentWidget(void);
private:
    RealTabWidget *realTabWidget;
    QPoint drag_pos;
signals:
	void widgetDnD(QWidget *src, QWidget *target);

public slots:

};

#endif // _TABBAR_H
