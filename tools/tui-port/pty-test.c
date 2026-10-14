#define _DEFAULT_SOURCE
#ifdef __HAIKU__
#include <bsd/pty.h>
#else
#include <pty.h>
#endif
#include <sys/select.h>
#include <sys/ioctl.h>
#include <sys/wait.h>
#include <unistd.h>
#include <signal.h>
#include <fcntl.h>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
int main(void) {
 int master,status,ready=0; char output[8192]={0}; size_t size=0;
 struct winsize dimensions={24,80,0,0};
 pid_t child=forkpty(&master,NULL,NULL,&dimensions);
 if(child<0){perror("forkpty");return 1;}
 if(child==0){execl("/bin/sh","sh","-c","test -t 0 || exit 3; stty size; printf 'PTY_READY\\n'; read line; stty size; printf 'UTF8 α β %s\\n' \"$line\"; exit 7",(char*)NULL);_exit(127);}
 for(int turns=0;turns<100;turns++){
  fd_set descriptors;FD_ZERO(&descriptors);FD_SET(master,&descriptors);
  struct timeval timeout={1,0};
  int available=select(master+1,&descriptors,NULL,NULL,&timeout);
  if(available<0){if(errno==EINTR)continue;break;}
  if(!available)continue;
  errno=0;
  ssize_t count=read(master,output+size,sizeof(output)-size-1);
  if(count<=0){printf("PTY_END read=%ld errno=%d (%s)\n",(long)count,errno,strerror(errno));printf("MASTER_FD_VALID flags=%d\n",fcntl(master,F_GETFD));break;}
  size+=count;output[size]=0;
  if(!ready&&strstr(output,"PTY_READY")){
   dimensions.ws_row=42;dimensions.ws_col=100;
   if(ioctl(master,TIOCSWINSZ,&dimensions)<0)break;
   if(write(master,"HELLO\n",6)!=6)break;
   ready=1;
  }
  if(size==sizeof(output)-1)break;
 }
 close(master);
 if(waitpid(child,&status,WNOHANG)==0){kill(child,SIGKILL);waitpid(child,&status,0);}
 printf("%s",output);
 if(!ready||!WIFEXITED(status)||WEXITSTATUS(status)!=7||!strstr(output,"24 80")||!strstr(output,"42 100")||!strstr(output,"UTF8 α β HELLO")){fprintf(stderr,"PTY_FAIL status=%d\n",status);return 1;}
 puts("PTY_PRIMITIVE_PASS: controlling tty, input/output, UTF-8, resize, EOF and child exit");return 0;
}
