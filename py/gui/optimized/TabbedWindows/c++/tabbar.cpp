#include "tabbar.h"
#include "realtabwidget.h"
#include <QDrag>
#include <QMimeData>
#include <QPixmap>
#include <QCursor>
#include <QDesktopWidget>

#include "dragpixmap.h"
#include "subwindow.h"
#include "twutil.h"

#define DRAG_OFFSET 100
#define PIXMAP_MAXWIDTH(current_width) \
		(QDesktopWidget().availableGeometry().width() / 5) > current_width ? current_width : \
		(QDesktopWidget().availableGeometry().width() / 5)
#define PIXMAP_OPACITY 0.60


TabBar::TabBar(RealTabWidget *parent) :
    QTabBar(parent)
{
	setObjectName("tabbar");
	connect(this, SIGNAL(destroyed()), twutil, SLOT(dumpDestroyed()));
	realTabWidget = parent;
}
QWidget* TabBar::currentWidget(void)
{
    return realTabWidget->widget(currentIndex());
}
void TabBar::mousePressEvent(QMouseEvent *event)
{
    if (event->button() == Qt::LeftButton)
        drag_pos = event->pos();
    QTabBar::mousePressEvent(event);
}
void TabBar::mouseMoveEvent(QMouseEvent *event)
{
	if(!(event->buttons() & Qt::LeftButton))
		return;
	if((event->pos() - drag_pos).manhattanLength() < DRAG_OFFSET)
        return;
	fn_begin;
	event->accept();
    QDrag *drag = new QDrag(this);
	/*DEBUG*/
	drag->setObjectName("drag");
	connect(drag, SIGNAL(destroyed()), twutil, SLOT(dumpDestroyed()));
    QMimeData *mimedata = new QMimeData();
    QWidget *widget = currentWidget();
    mimedata->setData("action", "window_drag");
    drag->setMimeData(mimedata);

	QPixmap pixmap = QPixmap::grabWidget(widget).scaledToWidth(
			PIXMAP_MAXWIDTH(widget->width()), Qt::SmoothTransformation);
	DragPixmap *dragpixmap = new DragPixmap(pixmap, PIXMAP_OPACITY, widget);
	connect(drag, SIGNAL(destroyed()), dragpixmap, SLOT(deleteLater()));
	dragpixmap->setObjectName("dragpixmap");
	connect(dragpixmap, SIGNAL(destroyed()), twutil, SLOT(dumpDestroyed()));
    dragpixmap->show();

    drag->exec();
	emit widgetDnD(currentWidget(), drag->target());
	QTabBar::mouseMoveEvent(event);
	fn_end;
}
