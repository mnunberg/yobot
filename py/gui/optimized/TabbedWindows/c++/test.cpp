#include <QApplication>
#include "tabcontainer.h"
#include "testwidget.h"

#ifdef TESTLIB
int main(int argc, char **argv) {
    QApplication *app =  new QApplication(argc, argv);
	TabContainer *t = new TabContainer();
	TestWidget *tw = TestWidget::newTestWidget(t, "first");
	TestWidget *tw2 = TestWidget::newTestWidget(t, "Second");
    t->show();
    t->resize(500,500);
    app->exec();
}
#endif
