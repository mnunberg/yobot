/*
 * yobotutil.h
 *
 *  Created on: Jul 17, 2010
 *      Author: mordy
 */

#ifndef YOBOTUTIL_H_
#define YOBOTUTIL_H_

/*
//#define copy_yotype_to_buf_and_increment(bufp,p,yotype) \
	memcpy(bufp,p,sizeof(yotype)); \
	bufp += sizeof(yotype);
*/
/*
//#define read_exact(fd,buf,size) \
	printf("EXPECTING SIZE: (int) %d\n",size); \
	assert(read(fd,buf,size)==size);
*/
#define must_succeed(f) if ((f)<=0) { perror(#f); exit(1); }

#define get_acct_from_id(id) g_hash_table_lookup(yobot_acct_table,GINT_TO_POINTER(id))

#ifdef WIN32
#define YOBOT_SET_SOCK_BLOCK(s, nonblock, status) \
{ unsigned long _argp = nonblock; \
status = ioctlsocket(s, FIONBIO, &_argp); }
#else

#define YOBOT_SET_SOCK_BLOCK(s, nonblock, status) \
	status = (nonblock) ? fcntl(s,F_SETFL,fcntl(s,F_GETFL) & ~O_NONBLOCK) :\
	fcntl(s,F_SETFL,fcntl(s,F_GETFL)|O_NONBLOCK);

#endif

#endif /* YOBOTUTIL_H_ */
