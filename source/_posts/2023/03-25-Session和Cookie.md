---
title: Session和Cookie
date: 2023-03-25 14:43:05
categories:
- [计算机网络]
tags:
- Session
- Cookie
---

我们知道HTTP协议是无状态的，那么在Web开发中如何做好用户的整个浏览过程的控制，最经典的解决方案就是使用Cookie和Session。
Cookie是客户端的机制，把用户数据缓存在客户端，而Session是服务端的机制，每个用户都会被分配一个唯一的SessionID，可以通过url传输或保存在客户端的Cookie中，也可以将Session保存在数据库中，比如Redis中。

## Session和Cookie是怎么来的？
假如你在浏览器上从来没有登录过GitHub，当你第一次登录的时候需要输入用户名和密码进行验证，通过验证后会调到个人首页，那么在登录成功后你点击你的某个代码仓库的时候服务器如何验证你的身份呢？因为HTTP协议是无状态的，服务器并不知道你上次已经验证过了，一种方法是每次请求都带上用户名和密码，这显然会导致用户体验极差。那么就需要再客户端或服务器上保存身份信息了，于是Cookie和Session就产生了。

### Cookie

#### Cookie原理
Cookie就是本地计算机保存一些用户操作的历史信息，用户再次访问时在HTTP请求头中带上Cookie信息，服务端就可以对其进行验证。
![](https://upload-images.jianshu.io/upload_images/14151453-e9dd7894922a2adb.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

#### 数据内容
Cookie本质上是由浏览器管理存储在客户端的一小段文本，Chrome浏览器可以使用EditThisCookie插件来管理Cookie，如下图所示。
![](https://upload-images.jianshu.io/upload_images/14151453-ae9b877211f0b906.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

#### 会话Cookie和持久Cookie
- 会话Cookie：Cookie是有有效期的，如果不设置过期时间，则表示这个Cookie的生命周期从创建到浏览器关闭为止，只要关闭浏览器Cookie就消失了，相当于数据保存在内存中，进程结束就丢失了
- 持久Cookie：如果设置了过期时间，浏览器会把Cookie数据保存到磁盘上，关闭浏览器再次打开依然有效，直到Cookie过期，浏览器通常都使用的持久Cookie。

### Session

#### Session原理
Session是服务器用来保存用户操作的历史信息的，使用SessionID来标识Session，SessionID由服务器产生，保证随机性和唯一性，相当于一个随机秘钥，避免在传输中暴露用户真实密码，但是服务器仍要将请求对Session进行对应，需要借助Cookie保存客户端的标识（SessionID）。
![](https://upload-images.jianshu.io/upload_images/14151453-849911fdca5ee4a5.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

当服务器需要对某个请求创建Session的时候，首先检查这个客户端的请求是否包含了SessionID，如果已经包含则表示次客户端之前已经创建过，只需要根据SessionID查询对应的Session。如果请求没有携带SessionID，则会生成一个Session和对应的SessionID，同时在本次响应中返回SessionID。

## 参考
【1】[build-web-application-with-golang](https://github.com/astaxie/build-web-application-with-golang/blob/master/zh/06.1.md)
