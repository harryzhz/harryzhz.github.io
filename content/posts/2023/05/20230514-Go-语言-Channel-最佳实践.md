---
title: Go 语言 Channel 最佳实践
slug: go-channel-best-practices
date: 2023-05-14 17:31:52
categories:
- Golang
tags:
- Go
---

## 简介

> Channel 基本概念介绍
> 
> 基本使用方法参见 [Go指南](https://tour.go-zh.org/concurrency/2)

Go 语言中的通道（channel）是一种特殊的类型。通道像一个传送带或者队列，总是遵循先入先出（First In First Out）的规则，保证收发数据的顺序。每一个通道都是一个具体类型的导管，也就是声明channel的时候需要为其指定元素类型。

### 不带缓冲的通道

创建不带缓冲的通道语法如下

```go
ch := make(chan int)
```

不带缓冲的通道发送和接收操作在另一端准备好之前都会阻塞，可以想象为是直接由发送者将数据传给接收者，没有中间缓冲区。这使得 Go 程可以在没有显式的锁或竞态变量的情况下进行同步。

### 带缓冲的通道

将缓冲长度作为第二个参数提供给 make 来初始化一个带缓冲的信道

```go
ch := make(chan int, 100)
```

仅当信道的缓冲区填满后，向其发送数据时才会阻塞。当缓冲区为空时，接受方会阻塞。

### 关闭通道

```go
close(ch)
```

发送者可通过 close 关闭一个信道来表示没有需要发送的值了。接收者可以通过为接收表达式分配第二个参数来测试信道是否被关闭：若没有值可以接收且信道已被关闭，那么在执行完 `v, ok := <-ch` 
之后 ok 会被设置为 false。

循环 `for i := range ch` 会不断从通道接收数据直到它被关闭

**注意：** 信道通常情况无需关闭，只有在必须告诉接收者不在有要发送的数据时才有必要关闭，不合理的关闭反而会带来各种问题，比如往一个已关闭的通道里写入数据导致 panic。因此很多 Channel 的使用教程会建议不要关闭通道，或者说只有发送者才能关闭通道

### select 通道

select 语句使一个 Go 程可以等待多个通信操作。select 会阻塞到某个分支可以继续执行为止，这时就会执行该分支。当多个分支都准备好时会随机选择一个执行。

```go
select {
case v <- ch1:
case v <- ch2:
case <-quit:
    return
}
```

## 应用场景

> Channel 的几种经典应用场景及示例

Channel 用于 Goroutine 之间的通信，常用于交换数据、并发控制、协程同步、超时控制等场景

### 1. 生产-消费模型

用来在生产者和消费者之前的数据传输，生产者协程将结果发送到通道，消费者协程从通道读取结果，生产者和消费者是并发进行的

```go
func producer(ch chan<- int) {
	defer close(ch)

	for i := 0; i < 5; i++ {
		time.Sleep(time.Second)
		fmt.Printf("[%s] Produced: %d\n", time.Now().Format(time.DateTime), i)
		ch <- i
	}
}

func consumer(ch <-chan int) {
	for {
		if v, ok := <-ch; ok {
			time.Sleep(time.Second)
			fmt.Printf("[%s] Consumed: %d\n", time.Now().Format(time.DateTime), v)
		} else {
			break
		}
	}
}

func TestProdConsume(t *testing.T) {
	ch := make(chan int, 5)

	go producer(ch)
	go consumer(ch)

	time.Sleep(10 * time.Second)
}
```

执行结果如下：
```md
=== RUN   TestProdConsume
[2023-05-15 00:35:58] Produced: 0
[2023-05-15 00:35:59] Produced: 1
[2023-05-15 00:35:59] Consumed: 0
[2023-05-15 00:36:00] Consumed: 1
[2023-05-15 00:36:00] Produced: 2
[2023-05-15 00:36:01] Consumed: 2
[2023-05-15 00:36:01] Produced: 3
[2023-05-15 00:36:02] Consumed: 3
[2023-05-15 00:36:02] Produced: 4
[2023-05-15 00:36:03] Consumed: 4
--- PASS: TestProdConsume (10.00s)
```

### 2. 限制并发数

当你有大量任务想通过 Goroutine 并发处理，但又不希望同时起太多 Goroutine 导致负载过高，可以通过 Channel 控制并发数量。

以下代码示例中，TotalNum 表示任务总数，ParallelNum 表示并发数

```go
func TestConcurrencyNumberLimit(t *testing.T) {
	const TotalNum = 10
	const ParallelNum = 2

	wg := &sync.WaitGroup{}
	// 限制并发数，缓冲区大小即为最大并发数
	ch := make(chan struct{}, ParallelNum)

	for i := 0; i < TotalNum; i++ {
		wg.Add(1)
		// 通道满时写入操作阻塞在这里，则不会继续起新的协程
		ch <- struct{}{}
		go func(idx int) {
			defer func() {
				wg.Done()
				<-ch
			}()

			fmt.Printf("[%s] process: %d/%d\n", time.Now().Format(time.DateTime), idx, TotalNum)
			time.Sleep(1 * time.Second)
		}(i + 1)
	}

	wg.Wait()
}
```

执行结果如下，可以看到并发数设置为 2 时每秒完成两个任务，10 个任务总共耗时 5 秒
```md
=== RUN   TestConcurrencyNumber
[2023-05-15 00:07:42] process: 2/10
[2023-05-15 00:07:42] process: 1/10
[2023-05-15 00:07:43] process: 3/10
[2023-05-15 00:07:43] process: 4/10
[2023-05-15 00:07:44] process: 5/10
[2023-05-15 00:07:44] process: 6/10
[2023-05-15 00:07:45] process: 7/10
[2023-05-15 00:07:45] process: 8/10
[2023-05-15 00:07:46] process: 9/10
[2023-05-15 00:07:46] process: 10/10
--- PASS: TestConcurrencyNumber (5.00s)
```

### 3. 超时控制

```go
func TestTimeout(t *testing.T) {
	ch := make(chan int, 1)

	// 执行一个耗时的任务
	go func() {
		time.Sleep(2 * time.Second)
		ch <- 1
	}()

	select {
	case res := <-ch:
		// 任务执行完毕
		fmt.Println("result: ", res)
	case <-time.After(1 * time.Second):
		// 任务执行超时
		fmt.Println("timeout")
	}
}
```

当任务耗时 2 秒，超时时间 1 秒时输出如下：
```md
=== RUN   TestTimeout
timeout
--- PASS: TestTimeout (1.00s)
```

当任务耗时 2 秒，超时时间 3 秒时输出如下：
```md
=== RUN   TestTimeout
result:  1
--- PASS: TestTimeout (2.00s)
```

## 如何优雅关闭通道

关于 "只能发送者关闭通道" 只是一种口头的约束，你可以在任何地方调用 `close` 方法来关闭通道，程序也可以编译运行。

实际上是发送者还是接收者关闭通道并没有太大影响，重点是通道的所有者，通常是创建通道的 Goroutine 做为所有者，负责管理通道的生命周期。

如果是一个发送者，可以直接由发送者关闭。
如果是多个发送者，希望所有发送者发送完毕再关闭通道，则需要有个额外的 Goroutine 来管理所有发送者，并在所有发送者结束后来关闭通道。代码示例如下：

```go
func TestCh(t *testing.T) {
	ch := make(chan int, 10)

	// 启动所有发送者协程
	wg := &sync.WaitGroup{}
	for i := 1; i < 10; i++ {
		wg.Add(1)
		go func(v int) {
			defer wg.Done()
			ch <- v
			fmt.Println("send:", v)
		}(i)
	}

	// 启动接受者协程
	quit := make(chan struct{})
	go func() {
        // 接收数据直到通道关闭
		for v := range ch {
			fmt.Println("receive:", v)
		}
		quit <- struct{}{}
	}()

	// 等待所有发送者协程结束，关闭通道
	wg.Wait()
	fmt.Println("send over...")
	close(ch)

	// 等待接收者协程结束
	<-quit
	fmt.Println("receive over!!!")
}
```
