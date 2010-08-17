/*yobotproto.i*/
%module yobotproto
%{
#include "yobotproto.h"
#include "protoclient.h"
%}
%include "cdata.i"
%include "cmalloc.i"
%include "cpointer.i"
%malloc(void);
%free(void);
%pointer_cast(char *, void *, tovoid);
%include yobotproto.h
%include protoclient.h
typedef long time_t;
typedef unsigned int uint32_t;
typedef unsigned short uint16_t;
typedef unsigned char uint8_t;
