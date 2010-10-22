#include "_tabbar.h"
#include "realtabwidget.h"
#include <QDrag>
#include <QMimeData>
#include <QPixmap>
#include <QCursor>
#include "dragpixmap.h"
#include "subwindow.h"
#include "twutil.h"

#define DRAG_OFFSET 100
#define PIXMAP_MAX_WIDTH 300
#define PIXMAP_OPACITY 0.60

#define fn_begin qDebug("%s: BEGIN", __PRETTY_FUNCTION__);
#define fn_end qDebug("%s: END", __PRETTY_FUNCTION__);


_TabBar::_TabBar(RealTabWidget *parent) :
    QTabBar(parent)
{
	setObjectName("****_tabbar****");
	connect(this, SIGNAL(destroyed()), twutil, SLOT(dumpDestroyed()));
	realTabWidget = parent;
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
	if(!(event->buttons() & Qt::LeftButton))
		return;
	if((event->pos() - drag_pos).manhattanLength() < DRAG_OFFSET)
        return;
	fn_begin;
	event->accept();
    QDrag *drag = new QDrag(this);
	/*DEBUG*/
	drag->setObjectName("****drag*****");
	connect(drag, SIGNAL(destroyed()), twutil,
			SLOT(dumpDestroyed()));
    QMimeData *mimedata = new QMimeData();
    QWidget *widget = currentWidget();
    mimedata->setData("action", "window_drag");
    drag->setMimeData(mimedata);
	QPixmap pixmap = QPixmap::grabWidget(widget).scaledToWidth(
			PIXMAP_MAX_WIDTH, Qt::SmoothTransformation);
	DragPixmap *dragpixmap = new DragPixmap(
			pixmap, PIXMAP_OPACITY, widget);
	connect(drag, SIGNAL(destroyed()), dragpixmap, SLOT(deleteLater()));
	dragpixmap->setObjectName("****dragpixmap****");
	connect(dragpixmap, SIGNAL(destroyed()),
			twutil, SLOT(dumpDestroyed()));
    dragpixmap->show();
    drag->exec();
	emit widgetDnD(currentWidget(), drag->target());
	QTabBar::mouseMoveEvent(event);
	fn_end;
}
