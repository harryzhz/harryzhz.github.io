---
title: 'Go 实战: 基于Thrift框架的 RPC 服务 Demo'
date: 2023-03-25 15:40:58
categories:
- Golang
tags:
- Go
- Thrift
- RPC
---
## Thrift架构简介
Thrift自顶向下可分为四层
1. Server(single-threaded, event-driven)服务器进程调度
2. Processor(compiler generated)RPC接口处理函数分发，IDL定义接口的实现将挂接到这里面
3. Protocol (JSON, compact etc)协议，定义数据传输格式
   - TBinaryProtocol（二进制格式）
   - TCompactProtocol（压缩格式）
   - TJSONProtocol （JSON格式）
   - TDebugProtocol （易看的文本格式，方便debug）

4. Transport(raw TCP, HTTP etc)网络传输，定义数据传输方式
   - TSocket（阻塞式socket）
   - TServerTransport（服务端模式，非阻塞socket）
   - TFramedTransport（以帧为单位，非阻塞式）
   - TMemoryTransport（内存形式）
   - TFileTransport（文件形式）
   - TZlibTransport（使用zlib压缩，与其他方式联合使用）

Thrift实际上是实现了C/S模式，通过代码生成工具将接口定义文件生成服务器端和客户端代码（可以为不同语言），从而实现服务端和客户端跨语言的支持。

## 开发环境
系统：macOS Big Sur 11.1
IDE ：GoLand 2020.3.4
Thrift：0.14.1

## 软件安装

### 安装thrift
```shell
brew install thrift # 安装
thrift -version # 查看版本检查是否安装成功
```

### 安装thrift support插件
Plugins->Marketplace搜索thrift support，安装后重启IDE即可
如果搜不到可以去[官网](https://plugins.jetbrains.com/plugin/14004-protocol-buffer-editor/versions)下载对应版本的安装包本地安装
![](https://upload-images.jianshu.io/upload_images/14151453-a18237de10e5fbcc.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

## 开发
### 编写thrift IDL
[IDL语法官方文档](https://thrift.apache.org/docs/idl.html)

user.thrift
```thrift

namespace go demo

struct User {
    1:required i32 id,
    2:required string name,
    3:required string avatar,
    4:required string address,
    5:required string mobile,
}

struct UserList {
    1:required list<User> userList,
    2:required i32 page,
    3:required i32 limit,
}
```
service.thrift
```thrift
include "user.thrift"

// 标记各语言的命名空间（包名），不同语言需要单独声明
namespace go demo

// 重新定义类型名称，同c语言
typedef map<string, string> Data

// 定义响应体结构
struct Response {
    1:required i32 errcode,
    2:required string errmsg,
    3:required Data data,
}

// 定义服务接口，相当于go的interface
service Greeter {
    Response SayHello(
        1:required user.User user
    )

    Response GetUser(
        1:required i32 uid
    )
}
```

### 生成目标语言代码
执行命令：`thrift -r --gen go service.thrift`
生成以下代码文件：
![](https://upload-images.jianshu.io/upload_images/14151453-309bcc4ed4fb76c6.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

### 编写golang服务端代码
服务端：
```go
package main

import (
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"github.com/apache/thrift/lib/go/thrift"
	"os"
	"thrift_practice/src/gen-go/demo"
)

func Usage() {
	fmt.Fprint(os.Stderr, "Usage of ", os.Args[0], ":\n")
	flag.PrintDefaults()
	fmt.Fprint(os.Stderr, "\n")
}

//定义服务
type Greeter struct {
}

//实现IDL里定义的接口
//SayHello
func (this *Greeter) SayHello(ctx context.Context, u *demo.User) (r *demo.Response, err error) {
	strJson, _ := json.Marshal(u)
	return &demo.Response{Errcode: 0, Errmsg: "success", Data: map[string]string{"User": string(strJson)}}, nil
}

//GetUser
func (this *Greeter) GetUser(ctx context.Context, uid int32) (r *demo.Response, err error) {
	return &demo.Response{Errcode: 1, Errmsg: "user not exist."}, nil
}

func main() {
	//命令行参数
	flag.Usage = Usage
	addr := flag.String("addr", "localhost:9090", "Address to listen to")
	flag.Parse()

	//protocol
	var protocolFactory thrift.TProtocolFactory
	protocolFactory = thrift.NewTBinaryProtocolFactoryDefault()

	//transport
	var transportFactory thrift.TTransportFactory
	transportFactory = thrift.NewTTransportFactory()

	//handler
	handler := &Greeter{}

	//transport,no secure
	var err error
	var transport thrift.TServerTransport
	transport, err = thrift.NewTServerSocket(*addr)
	if err != nil {
		fmt.Println("error running server:", err)
	}

	//processor
	processor := demo.NewGreeterProcessor(handler)

	fmt.Println("Starting the simple server... on ", *addr)

	//start tcp server
	server := thrift.NewTSimpleServer4(processor, transport, transportFactory, protocolFactory)
	err = server.Serve()

	if err != nil {
		fmt.Println("error running server:", err)
	}
}
```

客户端：（借助go testing）
```go
package main

import (
	"context"
	"fmt"
	"github.com/apache/thrift/lib/go/thrift"
	"testing"
	"thrift_practice/src/gen-go/demo"
)

var ctx = context.Background()

func GetClient() *demo.GreeterClient {
	addr := ":9090"
	var transport thrift.TTransport
	var err error
	transport, err = thrift.NewTSocket(addr)
	if err != nil {
		fmt.Println("Error opening socket:", err)
	}

	//protocol
	var protocolFactory thrift.TProtocolFactory
	protocolFactory = thrift.NewTBinaryProtocolFactoryDefault()

	//no buffered
	var transportFactory thrift.TTransportFactory
	transportFactory = thrift.NewTTransportFactory()

	transport, err = transportFactory.GetTransport(transport)
	if err != nil {
		fmt.Println("error running client:", err)
	}

	if err := transport.Open(); err != nil {
		fmt.Println("error running client:", err)
	}

	iprot := protocolFactory.GetProtocol(transport)
	oprot := protocolFactory.GetProtocol(transport)

	client := demo.NewGreeterClient(thrift.NewTStandardClient(iprot, oprot))
	return client
}

//GetUser
func TestGetUser(t *testing.T) {
	client := GetClient()
	rep, err := client.GetUser(ctx, 100)
	if err != nil {
		t.Errorf("thrift err: %v\n", err)
	} else {
		t.Logf("Recevied: %v\n", rep)
	}
}

//SayHello
func TestSayHello(t *testing.T) {
	client := GetClient()

	user := &demo.User{}
	user.Name = "thrift"
	user.Address = "address"

	rep, err := client.SayHello(ctx, user)
	if err != nil {
		t.Errorf("thrift err: %v\n", err)
	} else {
		t.Logf("Recevied: %v\n", rep)
	}
}
```

### 运行测试
1. 运行服务端代码
2. 运行客户端：`go test -v`
![](https://upload-images.jianshu.io/upload_images/14151453-ea5f1cec834f7b93.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

## 参考资料
【1】[从零开始基于go-thrift创建一个RPC服务](https://www.cnblogs.com/52fhy/p/11146047.html)
【2】[Go Tutorial](https://thrift.apache.org/tutorial/go.html)
【3】[Thrift RPC框架指南](https://www.kancloud.cn/digest/batu-go/153528)
