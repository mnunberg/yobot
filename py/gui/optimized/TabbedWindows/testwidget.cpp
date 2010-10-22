#include "testwidget.h"
#include <QMenuBar>
#include <QMenu>
#include <QAction>
#include <QPushButton>
#include <QVBoxLayout>
#include <QSizePolicy>

TestWidget::TestWidget(QWidget* parent, QString title) :
        SubWindow(parent, title)
{}

void TestWidget::setupWidgets(void)
{
    setWindowTitle(this->title);
    QMenuBar *menubar = new QMenuBar(this);
    QMenu *menu = new QMenu(QString("Title: ") + this->title);
    QAction *action_reproduce = new QAction("Reproduce", this);
    menu->addAction(action_reproduce);
    menubar->addMenu(menu);
    setMenuBar(menubar);
    menubar->setSizePolicy(QSizePolicy::Expanding, QSizePolicy::Fixed);
    setCentralWidget(new QWidget(this));
    centralWidget()->setLayout(new QVBoxLayout(centralWidget()));
    QPushButton *button = new QPushButton("Reproduce", this);
    button->setSizePolicy(QSizePolicy::Expanding, QSizePolicy::Expanding);
    centralWidget()->layout()->addWidget(button);
    connect(action_reproduce, SIGNAL(triggered()), SLOT(reproduce()));
    connect(button, SIGNAL(clicked()), SLOT(reproduce()));
}
void TestWidget::reproduce()
{
    if (tabcontainer) {
        counter++;
        newTestWidget(tabcontainer, QString().sprintf("%5d", counter));
    }
}

TestWidget *TestWidget::newTestWidget(TabContainer *tc, QString title)
{
    TestWidget *tw = new TestWidget(0, title);
    tw->setupWidgets();
    tw->init(tc);
    return tw;
}

int TestWidget::counter = 0;
