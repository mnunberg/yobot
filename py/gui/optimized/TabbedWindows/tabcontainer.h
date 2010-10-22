#ifndef TABCONTAINER_H
#define TABCONTAINER_H

#include <QMainWindow>
#include <QSet>
#include <QHash>
#include <QPointer>
/*forward declaration*/
class SubWindow;
class RealTabWidget;
#include "subwindow.h"
#include "realtabwidget.h"
class TabContainer : public QMainWindow
{
Q_OBJECT
public:
    explicit TabContainer(QWidget *parent = 0);
    static TabContainer* getContainer(void);
    static void addContainer(TabContainer*);
    static void removeContainer(TabContainer*);
    void dragEnterEvent(QDragEnterEvent *);
    void dropEvent(QDropEvent *);
    void closeEvent(QCloseEvent *);
    RealTabWidget *realTabWidget;
private:
    static QSet<TabContainer*> refs;
    QHash<QWidget*, QPointer<QMainWindow> > menuOwners;
signals:

public slots:
	void handleDnD(QWidget*,QWidget*);
    void rtwTabCloseRequested(int);
    void rtwCurrentChanged(int);
    void rtwSIG_TabRemoved(int);
};

#endif // TABCONTAINER_H
