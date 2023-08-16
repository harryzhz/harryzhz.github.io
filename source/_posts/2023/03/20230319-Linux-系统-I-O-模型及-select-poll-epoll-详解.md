---
title: Linux 系统 I/O 模型及 select/poll/epoll 详解
date: 2023-03-19 22:06:15
categories:
- 操作系统
tags:
- Linux
- I/O模型
- select/poll/epoll
---

## 基本概念说明
理解Linux的IO模型之前，首先要了解一些基本概念，才能理解这些IO模型设计的依据

### 用户空间和内核空间
操作系统使用虚拟内存来映射物理内存，对于32位的操作系统来说，虚拟地址空间为4G（2^32）。操作系统的核心是内核，为了保护用户进程不能直接操作内核，保证内核安全，操作系统将虚拟地址空间划分为内核空间和用户空间。内核可以访问全部的地址空间，拥有访问底层硬件设备的权限，普通的应用程序需要访问硬件设备必须通过**系统调用**来实现。

对于Linux系统来说，将虚拟内存的最高1G字节的空间作为内核空间仅供内核使用，低3G字节的空间供用户进程使用，称为用户空间。

### 进程的状态
- 就绪
- 阻塞
- 运行

### 进程切换

### 文件描述符fd

###  缓存I/O
又被称为标准I/O，大多数文件系统的默认I/O都是缓存I/O。在Linux系统的缓存I/O机制中，操作系统会将I/O的数据缓存在页缓存（内存）中，也就是数据先被拷贝到内核的缓冲区（内核地址空间），然后才会从内核缓冲区拷贝到应用程序的缓冲区（用户地址空间）。

这种方式很明显的缺点就是数据传输过程中需要再应用程序地址空间和内核空间进行多次数据拷贝操作，这些操作带来的CPU以及内存的开销是非常大的。

### 二I/O模式
由于Linux系统采用的缓存I/O模式，对于一次I/O访问，以读操作举例，数据先会被拷贝到内核缓冲区，然后才会从内核缓冲区拷贝到应用程序的缓存区，当一个read系统调用发生的时候，会经历两个阶段：
- 等待数据到来，进程处于阻塞状态
- 当数据准备就绪后，将数据从内核拷贝到用户进程，进程处于运行状态

正是因为这两个状态，Linux系统才产生了多种不同的网络I/O模式的方案

## Linux系统I/O模型
### 阻塞IO（blocking IO）
Linux系统默认情况下所有socke都是blocking的，一个读操作流程如下：
![](https://upload-images.jianshu.io/upload_images/14151453-5b4abb97fad3f18d.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

以UDP socket为例，当用户进程调用了recvfrom系统调用，如果数据还没准备好，应用进程被阻塞，内核直到数据到来且将数据从内核缓冲区拷贝到了应用进程缓冲区，然后向用户进程返回结果，用户进程才解除block状态，重新运行起来。

阻塞模行下只是阻塞了当前的应用进程，其他进程还可以执行，不消耗CPU时间，CPU的利用率较高。

### 非阻塞IO（nonblocking IO）
Linux可以设置socket为非阻塞的，非阻塞模式下执行一个读操作流程如下：
![](https://upload-images.jianshu.io/upload_images/14151453-485bfdc370909781.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

当用户进程发出recvfrom系统调用时，如果kernel中的数据还没准备好，recvfrom会立即返回一个error结果，不会阻塞用户进程，用户进程收到error时知道数据还没准备好，过一会再调用recvfrom，直到kernel中的数据准备好了，内核就立即将数据拷贝到用户内存然后返回ok，这个过程需要用户进程去轮询内核数据是否准备好。

非阻塞模型下由于要处理更多的系统调用，因此CPU利用率比较低。

### 信号驱动IO
应用进程使用sigaction系统调用，内核立即返回，等到kernel数据准备好时会给用户进程发送一个信号，告诉用户进程可以进行IO操作了，然后用户进程再调用IO系统调用如recvfrom，将数据从内核缓冲区拷贝到应用进程。流程如下：
![](https://upload-images.jianshu.io/upload_images/14151453-1f14b7a7da55a2bc.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

相比于轮询的方式，不需要多次系统调用轮询，信号驱动IO的CPU利用率更高。

### 异步IO
异步IO模型与其他模型最大的区别是，异步IO在系统调用返回的时候所有操作都已经完成，应用进程既不需要等待数据准备，也不需要在数据到来后等待数据从内核缓冲区拷贝到用户缓冲区，流程如下：
![](https://upload-images.jianshu.io/upload_images/14151453-95971297cce5bd98.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)
在数据拷贝完成后，kernel会给用户进程发送一个信号告诉其read操作完成了。

### IO多路复用
是用select、poll等待数据，可以等待多个socket中的任一个变为可读，这一过程会被阻塞，当某个套接字数据到来时返回，之后再用recvfrom系统调用把数据从内核缓存区复制到用户进程，流程如下：
![](https://upload-images.jianshu.io/upload_images/14151453-8845990e0d75eb9a.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

流程类似阻塞IO，甚至比阻塞IO更差，多使用了一个系统调用，但是IO多路复用最大的特点是让单个进程能同时处理多个IO事件的能力，又被称为事件驱动IO，相比于多线程模型，IO复用模型不需要线程的创建、切换、销毁，系统开销更小，适合高并发的场景。

####  select
select是IO多路复用模型的一种实现，当select函数返回后可以通过轮询fdset来找到就绪的socket。
```c
int select(int n, fd_set *readfds, fd_set *writefds, fd_set *exceptfds, struct timeval *timeout)
```

优点是几乎所有平台都支持，缺点在于能够监听的fd数量有限，Linux系统上一般为1024，是写死在宏定义中的，要修改需要重新编译内核。而且每次都要把所有的fd在用户空间和内核空间拷贝，这个操作是比较耗时的。

#### poll
poll和select基本相同，不同的是poll没有最大fd数量限制（实际也会受到物理资源的限制，因为系统的fd数量是有限的），而且提供了更多的时间类型。
```c
int poll(struct pollfd *fds, unsigned int nfds, int timeout)
```

总结：select和poll都需要在返回后通过轮询的方式检查就绪的socket，事实上同时连的大量socket在一个时刻只有很少的处于就绪状态，因此随着监视的描述符数量的变多，其性能也会逐渐下降。

#### epoll
epoll是select和poll的改进版本，更加灵活，没有描述符限制。epoll使用一个文件描述符管理多个描述符，将用户关系的文件描述符的事件存放到内核的一个事件表中，这样在用户空间和内核空间的copy只需一次。
```c
int epoll_create(int size)
int epoll_ctl(int epfd, int op, int fd, struct epoll_event *event)
int epoll_wait(int epfd, struct epoll_event * events, int maxevents, int timeout)
```
epoll_create()用来创建一个epoll句柄。
epoll_ctl() 用于向内核注册新的描述符或者是改变某个文件描述符的状态。已注册的描述符在内核中会被维护在一棵红黑树上，通过回调函数内核会将 I/O 准备好的描述符加入到一个就绪链表中管理。
 epoll_wait() 可以从就绪链表中得到事件完成的描述符，因此进程不需要通过轮询来获得事件完成的描述符。

##### LT模式（水平触发，默认）
当epoll_wait检测到描述符IO事件发生并且通知给应用程序时，应用程序可以不立即处理该事件，下次调用epoll_wait还会再次通知该事件，支持block和nonblocking socket。

##### ET模式（边缘触发）
当epoll_wait检测到描述符IO事件发生并且通知给应用程序时，应用程序需要立即处理该事件，如果不立即处理，下次调用epoll_wait不会再次通知该事件。

ET模式在很大程度上减少了epoll事件被重复触发的次数，因此效率要比LT模式高。epoll工作在ET模式的时候，必须使用nonblocking socket，以避免由于一个文件句柄的阻塞读/阻塞写操作把处理多个文件描述符的任务饿死。

#### 应用场景
- select的timeout参数精度为微妙，而poll和epoll都是毫秒，会因此select更加适合对实时性要求比较高的场景

- poll 没有最大描述符数量的限制，如果平台支持并且对实时性要求不高，应该使用 poll 而不是 select。

- epoll适合高并发的场景，有大量描述符需要同时监听，并且最好是长连接。
不适合监控的描述符状态变化频繁且短暂，因为epoll的描述符都存在内核中，每次对其状态修改都要通过epoll_ctl系统调用来实现，频繁的系统调用导致频繁在内核态和用户态切换，会大大降低性能。

## 参考
【segmentfault】[Linux IO模式及 select、poll、epoll详解](https://segmentfault.com/a/1190000003063859)
【GitHub】[CyC2018/CS-Notes](https://github.com/CyC2018/CS-Notes/blob/master/notes/Socket.md#%E4%B8%80io-%E6%A8%A1%E5%9E%8B)