/*Source*/

#include "dragpixmap.h"
#include <QDesktopWidget>
#include <QTimer>
#include <QPushButton>
#include <QApplication>
#include <QPixmap>

#define CURSOR_OFFSET 25

DragPixmap::DragPixmap(QPixmap pixmap, qreal opacity=0.40, QWidget *parent=0) :
    QLabel(parent)
{
    setAlignment(Qt::AlignTop|Qt::AlignLeft);
    setPixmap(pixmap);
    setWindowFlags(Qt::FramelessWindowHint|Qt::Dialog);
    setWindowOpacity(opacity);
    orig_size = pixmap.size();
    screen_geometry = QDesktopWidget().availableGeometry();
    QTimer *timer = new QTimer(this);
    timer->setInterval(20);
    connect(timer, SIGNAL(timeout()), this, SLOT(updatepos()));
    timer->start();
}
void DragPixmap::updatepos(void) {
    static bool isShrinked = false;
    setUpdatesEnabled(false);
    QPoint _pos = QCursor().pos();
    QRect _geometry = geometry();
    _geometry.moveTo(_pos.x() + CURSOR_OFFSET, _pos.y() + CURSOR_OFFSET);
    QRect intersected = _geometry.intersected(screen_geometry);
    if (intersected != _geometry) {
        _geometry = intersected;
        isShrinked = true;
        goto do_resize;
    }
    if (isShrinked) {
        _geometry.setSize(orig_size);
        intersected = _geometry.intersected(screen_geometry);
        if (intersected != _geometry) {
            isShrinked = true;
            _geometry = intersected;
        } else {
            isShrinked = false;
        }
        goto do_resize;
    }
    do_resize:
    if (_geometry.intersects(screen_geometry))
        setGeometry(_geometry);
    setUpdatesEnabled(true);
}


#ifdef MAIN_APP
int main(int argc, char *argv[]) {
    QApplication *app = new QApplication(argc, argv);
    QPushButton *button = new QPushButton("Hello World");
    button->setSizePolicy(QSizePolicy::Expanding, QSizePolicy::Expanding);
    button->resize(400, 400);
    button->show();
    QPixmap pixmap = QPixmap::grabWidget(button);
    DragPixmap *dragpixmap = new DragPixmap(pixmap, 0.53, 0);
    dragpixmap->show();
    app->exec();

}
#endif
