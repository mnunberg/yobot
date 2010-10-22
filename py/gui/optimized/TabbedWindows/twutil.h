#ifndef TWUTIL_H
#define TWUTIL_H

#include <QObject>

class TWUtil : public QObject
{
Q_OBJECT
public:
    explicit TWUtil(QObject *parent = 0);
signals:

public slots:
	 void dumpDestroyed(void);
	 void logCreation(QObject*);
};

extern TWUtil *twutil;

#endif // TWUTIL_H

