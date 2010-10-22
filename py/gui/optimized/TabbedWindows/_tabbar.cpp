#include "_tabbar.h"
#include "realtabwidget.h"
#include <QDrag>
#include <QMimeData>
#include <QPixmap>
#include <QCursor>
#include "dragpixmap.h"
#include "subwindow.h"

#define DRAG_OFFSET 100
#define PIXMAP_MAX_WIDTH 300
#define PIXMAP_OPACITY 0.60


_TabBar::_TabBar(RealTabWidget *parent) :
    QTabBar(parent)
{
    setAcceptDrops(true);
    this->realTabWidget = parent;
}
QWidget* _TabBar::currentWidget(void)
{
    return realTabWidget->widget(currentIndex());
}
void _TabBar::mousePressEvent(QMouseEvent *event)
{
    if (event->button() == Qt::LeftButton)
        drag_pos = event->pos();
    QTabBar::mousePressEvent(event);
}
void _TabBar::mouseMoveEvent(QMouseEvent *event)
{
    if(!(event->buttons() & Qt::LeftButton)) {
        return;
    }
    if((event->pos() - drag_pos).manhattanLength() < DRAG_OFFSET) {
        return;
        }
    QDrag *drag = new QDrag(this);
    QMimeData *mimedata = new QMimeData();
    QWidget *widget = currentWidget();
    mimedata->setData("action", "window_drag");
    drag->setMimeData(mimedata);
    QPixmap pixmap = QPixmap::grabWidget(widget).scaledToWidth(PIXMAP_MAX_WIDTH,
                                                               Qt::SmoothTransformation);
    DragPixmap *dragpixmap = new DragPixmap(pixmap, PIXMAP_OPACITY, widget);
    dragpixmap->move(event->pos());
    dragpixmap->show();
    drag->exec();
    TabContainer *tc = qobject_cast<TabContainer*>(drag->target());
    dragpixmap->deleteLater();
    if(!tc) {
        qDebug("%s: did not get a valid target %p, detaching",
               __func__, drag->target());
        detachWidget();
    } else {
        qDebug("%s: dropped on TabContainer %p", __func__, tc);
    }
}

void _TabBar::detachWidget(void)
{
    qDebug(__func__);
    SubWindow *subwindow = qobject_cast<SubWindow*>(currentWidget());
    if(!subwindow) {
        qDebug("Expected SubWindow instance!");
        qDebug("dumping object information");
        currentWidget()->dumpObjectInfo();
        return;
    }
    QSize oldsize;
    QWidget *oldparent;
    qDebug("%s: oldparent: %p", __func__, oldparent);
    if (subwindow->tabcontainer) {
        oldsize = subwindow->tabcontainer->size();
        oldparent = subwindow->tabcontainer->parentWidget();
    } else {
        oldsize = subwindow->size();
        oldparent = 0;
    }
    TabContainer *tc = new TabContainer(oldparent);
//    TabContainer *tc = new TabContainer();
    subwindow->addToContainer(tc);
    tc->show();
    tc->resize(oldsize);
    tc->move(QCursor().pos());
}
