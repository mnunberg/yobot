#ifndef DRAGPIXMAP_H
#define DRAGPIXMAP_H

#include <QLabel>

class DragPixmap : public QLabel
{
Q_OBJECT
public:
    explicit DragPixmap(QPixmap,qreal,QWidget*);
private:
    QSize orig_size;
    QRect screen_geometry;
private slots:
    void updatepos(void);
signals:

public slots:

};

#endif // DRAGPIXMAP_H
