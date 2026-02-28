---
title: 'Linux进程管理:supervisor和nohup原理及使用'
slug: linux-process-management-supervisor-nohup
date: 2023-03-13 08:49:37
categories:
- 操作系统
tags:
- Linux
- 守护进程
---

## 原理

### 守护进程（daemon）
守护进程是一类在后台运行的特殊进程，用于执行特定的系统任务。他独立于控制终端并且周期性的执行某种任务或等待处理某些发生的事件。Linux系统的大多数服务器就是通过守护进程实现的。
常见的守护进程包括：
- 系统日志进程syslogd
- Web服务器httpd
- 邮件服务器sendmail
- 数据库服务器mysqld等

守护进程一般在系统启动时开始运行，除非强行终止，否则会持续运行知道系统关机，通常以超级用户（root）权限运行。

### 前台任务与后台任务
假如有个简单的go的web服务器程序，使用如下方式启动，称为前台任务。独占了命令窗口，只有运行完了或手动终止（Ctrl+C），才能执行其他命令。
![](https://upload-images.jianshu.io/upload_images/14151453-ec0b4b889fe10808.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

如果以如下方式，在命令结尾加上符号`&`，启动的进程就会称为后台任务。
![](https://upload-images.jianshu.io/upload_images/14151453-35d2076e46e71ac5.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)
后台任务又如下特点：
- 继承当前session的标准输出(stdout)和标准错误(stderr)，因此如上图所示，后台任务的所有输出仍会同步的在命令行显示
- 不再继承当前session的标准输入(stdin)，无法向这个任务输入指令，如果它试图读取标准输入，就会暂停执行（halt）

### SIGHUP信号
变为后台任务并不代表进程成为了守护进程，因为当session关闭后，后台任务就会终止。Linux系统终端session退出流程如下：
1. 用户准备退出session
2. 系统向改session发送`SIGHUP`信号
3. session将`SIGHUP`信号发送给所有子进程
4. 子进程收到`SIGHUP`信号后会自动退出

## nohup
nohup 是后台作业的意思， nohup运行的进程将会忽略终端信号运行。即后台运行一个命令。nohup COMMAND & 用nohup运行命令可以使命令永久的执行下去，和用户终端没有关系，例如我们断开SSH连接都不会影响它的运行。

使用nohup命令的方式可以启动一个守护进程，如下图所示：
![](https://upload-images.jianshu.io/upload_images/14151453-a2bafec78cb93512.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

nohup命令对进程做了如下操作：
- 忽略`SIGHUP`信号，因此当session关闭进程就不会退出
- 关闭标准输入，该进程不再接收任何输入，即使运行在前台
- 重定向标准输出和标准错误到文件nohup.out（默认情况，可以指定输出的文件）

nohup不会自动把进程变为后台任务，所以必须加上`&`。

## supervisor
supervisor是用Python开发的一套通用的进程管理程序，能将一个普通的命令行进程变为后台daemon，并监控进程状态，异常退出时能自动重启。
supervisor管理进程是通过fork/exec的方式把被管理的进程当做子进程来启动，用户只需要在配置文件中将要管理的进程进行配置。

### 结构
supervisor主要由Supervisord、Supervisorctl、Web server和XML-RPC interface组成：
- supervisord：主进程，负责管理进程的server，它会根据配置文件创建指定数量的应用程序的子进程，管理子进程的整个生命周期，对crash的进程重启，对进程变化发送事件通知等。同时通过内置web server和XML-RPC Interface可以轻松实现进程管理。
- supervisorctl：管理client，用户通过命令行发送消息给supervisord，可以查看进程状态，加载配置文件，启停进程，查看进程标准输出和错误输出，远程操作等。
- Web server：superviosr提供了web server功能，可通过web控制进程。
- XML-RPC interface： XML-RPC接口，提供XML-RPC服务来对子进程进行管理和监控。

### macOS环境安装使用

#### 安装并启动
```shell
$ brew install supervisor
$ brew services start supervisor
```
#### 创建配置目录和配置文件
默认的配置文件路径为`/usr/local/etc/supervisord.conf`，查看该文件可以看到如下内容：
```shell
$ tail -n2 /usr/local/etc/supervisord.conf
[include]
files = /usr/local/etc/supervisor.d/*.ini
```
可以看到include了`/usr/local/etc/supervisor.d/`目录下的`.ini`文件，因此我们需要创建改目录，然后对要管理的进程或进程组创建对应的`.ini`格式的配置文件
```shell
$ mkdir -pv /usr/local/etc/supervisor.d
$ vim /usr/local/etc/supervisor.d/myserver.ini
```
编辑配置文件内容如下：
```shell
[program:server]
process_name=%(program_name)s_%(process_num)02d
command=/usr/local/go/bin/go run /Users/harryzhang/go/src/server/server.go # 要执行的命令
autostart=true # 系统开机自动启动
autorestart=true # 进程终止自动重启
user=harryzhang # 用户
numprocs=1 # 启动进程数
redirect_stderr=true # 是否将标准错误重定向到标准输出
stdout_logfile=/Users/harryzhang/go/src/server/server.log # 指定标准输出保存的文件路径
```

#### 重启supervisor
编辑好配置文件后重启supervisor就可以生效，可以使用supervisorctl命令查看和管理进程状态。
```shell
$ brew services restart supervisor
Stopping `supervisor`... (might take a while)
==> Successfully stopped `supervisor` (label: homebrew.mxcl.supervisor)
==> Successfully started `supervisor` (label: homebrew.mxcl.supervisor)

$ supervisorctl status
server:server_00                 RUNNING   pid 41382, uptime 0:00:04
```
如果指定的命令执行没有异常，会看到进程已处于运行状态，如果没有处于运行状态，可以查看日志文件，可能为命令执行出错直接退出了。

## 参考
【1】[Linux 守护进程的启动方法](http://www.ruanyifeng.com/blog/2016/02/linux-daemon.html)

【2】[进程管理工具supervisor 和 nohup](https://segmentfault.com/a/1190000017370468)
