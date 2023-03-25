---
title: 什么是WebSocket？
date: 2023-03-25 14:42:47
categories:
- [计算机网络]
tags:
- "WebSocket"
---

## 基本概念
WebSocket是一种网络通信协议，是HTML5新增的特性，实现了基于浏览器的远程socket，使浏览器和服务器可以进行全双工通信，大部分浏览器都对此做了支持。
WebSocket的URL格式形如：ws://localhost:80/、wss://localhost:443/

## 为什么有了HTTP协议还要WebSocket
HTTP协议采用的是客户端（浏览器）轮询的方式，即客户端发送请求，服务端做出响应，为了获取最新的数据，需要不断的轮询发出HTTP请求，占用大量带宽。
WebSocket采用了一些特殊的报头，使得浏览器和服务器只需要通过“握手”建立一条连接通道后，此链接保持活跃状态，之后的客户端和服务器的通信都使用这个连接，解决了Web实时性的问题，相比于HTTP有一下好处：
- 一个Web客户端只建立一个TCP连接
- WebSocket服务端可以主动推送（push）数据到Web客户端
- 有更加轻量级的头，减少了数据传输量

## WebSocket原理
![](https://upload-images.jianshu.io/upload_images/14151453-83f761a12847fa76.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

### 建立连接
WebSocket建立连接必须由浏览器发起，是一个标准的HTTP请求，如下图所示
![](https://upload-images.jianshu.io/upload_images/14151453-0f3bd32d35e06362.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)
#### 请求
1. 请求地址以`ws://`开头
2. 请求头`Upgrade: websocket`和`Connection:Upgrade`表示要将这个连接转换为WebSocket连接
3. `Sec-WebSocket-Key`用于标识连接，是一个base64编码的字符串
4. `Sec-WebSocket-Version`指定了WebSocket协议版本

#### 响应
1. 响应状态码`101`表示本次连接的HTTP协议将被更改
2. `Upgrade: websocket`表示更改后的协议是WebSocket
3. `Sec-WebSocket-Accept`通过如下方式计算：
- 对请求头的`Sec-WebSocket-Key`字符串加上一个固定的字符串，例如：
`H+VLjR1wb4JQ62TmabK87g==258EAFA5-E914-47DA-95CA-C5AB0DC85B11`
- 然后对该字符串用sha1算法散列出二进制值，再对其进行base64加密，例如：
`ccJoRDcGOFzCVrIwpX/qF3BoIN0=`

### 数据格式
WebSocket的协议比较简单，在第一次handshake通过之后，连接建立成功，之后的通讯数据都是以"\x00"开头，以"\xFF"结尾，对客户端来说这个是透明的，WebSocket的实现组件会对原始数据掐头去尾。

### 特点
1. 建立在TCP协议只上，服务端比较容易实现
2. 于HTTP协议有良好的兼容性，默认端口也是80和443，握手阶段使用HTTP协议，因此握手时不容易屏蔽，能通过各种HTTP代理服务器
3. 数据格式轻量，通信高效且节省带宽
4. 支持传输文本数据和二进制数据
5. 没有同源限制，客户端可以与任意服务器通信
6. 也支持加密传输，WS+SSL，URL形如`wss://`

## Go语言实现
go的标准SDK中没有支持WebSocket，但是官方维护的net子包中支持
`go get golang.org/x/net/websocket`
### 客户端
```html
<!DOCTYPE html>
<html>
<head></head>
<body>
<script type="text/javascript">
    var sock = null;
    var wsuri = "ws://127.0.0.1:7777";

    window.onload = function() {

        console.log("onload");

        sock = new WebSocket(wsuri);

        sock.onopen = function() {
            console.log("connected to " + wsuri);
        }

        sock.onclose = function(e) {
            console.log("connection closed (" + e.code + ")");
        }

        sock.onmessage = function(e) {
            console.log("message received: " + e.data);
        }
    };

    function send() {
        var msg = document.getElementById('message').value;
        sock.send(msg);
    };
</script>
<h1>WebSocket Echo Test</h1>
<form>
    <p>
        Message: <input id="message" type="text" value="Hello, world!">
    </p>
</form>
<button onclick="send();">Send Message</button>
</body>
</html>
```
客户端JavaScript代码，通过`new WebSocket(wsuri)`创建了一个WebSocket连接，握手成功后会触发onopen事件，客户端绑定了四个事件：
- onopen：建立连接后触发
- onmessage：收到消息后触发
- onerror：发生错误时触发
- onclose：关闭连接时触发

### 服务端
```go
package main

import (
	"golang.org/x/net/websocket"
	"log"
	"net/http"
)

func handleEcho(ws *websocket.Conn) {
	var err error

	for {
		var reply string

		if err = websocket.Message.Receive(ws, &reply); err != nil {
			log.Println("[server] Can't receive")
			break
		}
		log.Println("[server] Received from client:", reply)

		msg := "welcome: " + reply
		if err = websocket.Message.Send(ws, msg); err != nil {
			log.Println("[server] Can't Send")
			break
		}
		log.Println("[server] Send to client:", msg)
	}
}

func main() {
	http.Handle("/", websocket.Handler(handleEcho))
	log.Println("[server] listen in 127.0.0.1:7777")
	if err := http.ListenAndServe(":7777", nil); err != nil {
		log.Fatal("[server] ListenAndServe:", err)
	}
}

```
运行后在客户端页面点击Send Message按钮，可以看到服务端如下响应：
![](https://upload-images.jianshu.io/upload_images/14151453-e2ef3c1cb34f117d.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

## 参考资料
【1】[build-web-application-with-golang](https://github.com/astaxie/build-web-application-with-golang/blob/master/zh/08.2.md)
【2】[廖雪峰：WebSocket](https://www.liaoxuefeng.com/wiki/1022910821149312/1103303693824096)
【3】[阮一峰：WebSocket教程](https://www.ruanyifeng.com/blog/2017/05/websocket.html)
