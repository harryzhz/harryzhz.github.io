---
title: 'Go 实战: Socket 编程'
date: 2023-03-25 15:40:10
categories:
- [Golang]
tags:
- Socket
- Go
---
## Socket如何通信
在网络中要唯一确定一个进程需要用一个三元组（Protocol，IP，Port），IP地址唯一确定一台主机，再通过协议和端口唯一确定一个进程，这里也可以看到TCP和UDP可以绑定同一个端口。能唯一确定网络中的进程了，便可以利用这个标志在他们之间进行数据交互。

## Socket基础

### TCP/IP
Go支持的IP类型
- IPv4
- IPv6

Go支持的协议类型
- TCP
- UDP

## Go Socket编程
Go语言的net包对TCP和UDP协议提供了支持，可以借助net改包方便的开发Socket应用

### TCP Socket
TCP客户单和服务端通信时需要建立一个连接，Go语言的net包中`TCPConn`类型就表示一个TCP连接，主要有以下两个函数，用来读写数据：
```go
func (c *TCPConn) Write(b []byte) (int, error)
func (c *TCPConn) Read(b []byte) (int, error)
```

客户端建立连接需要知道服务器的地址，net表中的`TCPAddr`类型表示一个TCP的地址信息，定义如下：
```go
type TCPAddr struct {
	IP IP
	Port int
	Zone string // IPv6 scoped addressing zone
}
```
可以使用`ResolveTCPAddr`获取一个`TCPAddr`
```go
func ResolveTCPAddr(net, addr string) (*TCPAddr, os.Error)
```

#### 常用的控制TCP连接相关函数

- `func DialTimeout(net, addr string, timeout time.Duration) (Conn, error)`
设置连接超时，客户端和服务端都适用，超过设置时间返回连接失败

- `func (c *TCPConn) SetReadDeadline(t time.Time) error`
  `func (c *TCPConn) SetWriteDeadline(t time.Time) error`
设置读写超时

- `func (c *TCPConn) SetKeepAlive(keepalive bool) os.Error`
设置keepAlive属性。操作系统层在tcp上没有数据和ACK的时候，会间隔性的发送keepalive包，操作系统可以通过该包来判断一个tcp连接是否已经断开，在windows上默认2个小时没有收到数据和keepalive包的时候认为tcp连接已经断开，这个功能和我们通常在应用层加的心跳包的功能类似。

#### TCP Server

服务端要做的事如下：
1. 监听一个地址端口
2. 调用accept（阻塞）等待连接
3. 当请求到来时接受请求并读写数据
4. 数据交互完成后关闭连接

##### 示例
根据客户端发送的数据来返回不同格式的当前时间，使用goroutine支持并发请求。
server.go
```go
package main

import (
	"fmt"
	"log"
	"net"
	"os"
	"strconv"
	"strings"
	"time"
)

func main() {
	service := "localhost:7777"
	tcp_addr, err := net.ResolveTCPAddr("tcp4", service)
	checkError(err)
	// 监听本地7777端口
	listener, err := net.ListenTCP("tcp", tcp_addr)
	checkError(err)
	for {
		log.Println("[server] listening", tcp_addr.String())
		// 等待客户端连接
		conn, err := listener.Accept()
		if err != nil {
			continue
		}
		go handleDatetime(conn)
	}
}

// 事件处理
func handleDatetime(conn net.Conn)  {
	// 设置读超时
	conn.SetReadDeadline(time.Now().Add(10 * time.Second))
	defer conn.Close()

	for {
		buffer := make([]byte, 128)
		read_len, err := conn.Read(buffer)

		if err != nil {
			fmt.Println(err)
			break
		}

		// 根据读到的数据返回对应的时间格式
		if read_len == 0 {
			break
		} else if strings.TrimSpace(string(buffer[:read_len])) == "timestamp" {
			daytime := strconv.FormatInt(time.Now().Unix(), 10)
			conn.Write([]byte(daytime))
		} else {
			daytime := time.Now().String()
			conn.Write([]byte(daytime))
		}
		log.Println("[server] response to:", conn.RemoteAddr().String())
	}
}

func checkError(err error) {
	if err != nil {
		fmt.Fprintf(os.Stderr, "Fatal error: %s", err.Error())
		os.Exit(1)
	}
}
```
运行结果如下：
![server.png](https://upload-images.jianshu.io/upload_images/14151453-e08a5bf26d08e2c3.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

#### TCP Client

客户端要做的事如下：
1. 向服务端发起连接请求
3. 发送数据到服务端，接收来自服务端的响应数据
4. 数据交互完成后关闭连接

##### 示例
client.go
```go
package main

import (
	"flag"
	"fmt"
	"net"
	"os"
)

func main() {
	service := flag.String("host", "127.0.0.1:7777", "an ip address")
	flag.Usage = func() {
		fmt.Fprintf(os.Stdout, "Usage of %s:\n", "mock http request")
		flag.PrintDefaults()
	}
	flag.Parse()

	tcp_addr, err := net.ResolveTCPAddr("tcp4", *service)
	checkError(err)
	// 发起连接请求
	conn, err := net.DialTCP("tcp", nil, tcp_addr)
	checkError(err)

	// 读写数据
	_, err = conn.Write([]byte("timestamp\\r\\n"))
	checkError(err)
	buffer := make([]byte, 256)
	_, err = conn.Read(buffer)
	checkError(err)
	fmt.Println("[client] receive from:", conn.RemoteAddr().String())
	fmt.Println(string(buffer))
	
	// 关闭连接
	conn.Close()
	os.Exit(0)
}

func checkError(err error) {
	if err != nil {
		fmt.Fprintf(os.Stderr, "Fatal error: %s", err.Error())
		os.Exit(1)
	}
}
```
在服务端运行的前提下，运行客户端后结果如下：
客户端：
![client.png](https://upload-images.jianshu.io/upload_images/14151453-6eeaa68e245bb6d4.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

服务端：
![server.png](https://upload-images.jianshu.io/upload_images/14151453-72e43bfb22b5a3ad.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)


## 参考资料
【1】[**GitHub/astaxie**](https://github.com/astaxie)/[build-web-application-with-golang-8.1 Socket编程](https://github.com/astaxie/build-web-application-with-golang/blob/master/zh/08.1.md)
