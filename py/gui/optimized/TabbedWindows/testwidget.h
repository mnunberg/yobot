#ifndef TESTWIDGET_H
#define TESTWIDGET_H
#include "subwindow.h"
#include "tabcontainer.h"
class TestWidget : public SubWindow
{
Q_OBJECT;
public:
    explicit TestWidget(QWidget*,QString);
    void setupWidgets(void);
    static TestWidget* newTestWidget(TabContainer *tc, QString title);
private:
    static int counter;
public slots:
    void reproduce(void);
};

#endif // TESTWIDGET_H
