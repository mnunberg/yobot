#ifndef REALTABWIDGET_H
#define REALTABWIDGET_H

#include <QTabWidget>
#include <QSet>
class RealTabWidget : public QTabWidget
{
Q_OBJECT
public:
    explicit RealTabWidget(QWidget *parent = 0);
    void addTab(QWidget*, QString);
    void removeTab(int);
    void tabRemoved(int index);
    void tabInserted(int index);
    QSet<QWidget*> tabIds;
private:
signals:
    void SIG_tabRemoved(int);
    void SIG_tabInserted(int);
public slots:

};

#endif // REALTABWIDGET_H
