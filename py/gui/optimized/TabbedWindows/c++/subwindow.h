#ifndef SUBWINDOW_H
#define SUBWINDOW_H

#include <QMainWindow>
#include "tabcontainer.h"
class TabContainer;

class SubWindow : public QMainWindow
{
Q_OBJECT
public:
    explicit SubWindow(QWidget *parent, QString title);
    TabContainer *tabcontainer;
    void removeFromContainer(void);
    void addToContainer(TabContainer*);
    QString title;
    void init(TabContainer *tc);
    void activateWindow();
    void keyPressEvent(QKeyEvent *);
signals:

public slots:

};

#endif // SUBWINDOW_H
