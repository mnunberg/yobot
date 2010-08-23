#ifndef FN_OVERRIDE_H
#define FN_OVERRIDE_H_
int yb_fn_override_by_name(const char *orig, const char *target, const char *libname);
int yb_fn_override_by_ptr(void *orig, const void *target);
#endif /*FN_OVERRIDE_H_*/
