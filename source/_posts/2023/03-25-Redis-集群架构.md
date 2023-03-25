---
title: Redis 集群架构
date: 2023-03-25 15:04:57
categories:
- [缓存]
tags:
- Redis
- Redis 集群
---

单实例往往不能满足生产环境的需求，需要引入Redis集群，比较常见的Redis集群方案有主从复制、哨兵模式、官网的Redis Cluster，另外还有一些Proxy模式，各大厂商也有自己的方案。

## 主从复制模式
#### 基本架构
![](https://upload-images.jianshu.io/upload_images/14151453-e32695d0c4b0efc5.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

#### 工作原理
1. slave向master发送SYNC命令，master接收到命令后通过bgsave保存快照（RDB持久化），并使用缓冲区记录保存快照期间执行的写命令
2. master将快照文件发送给slave，继续往缓冲区记录写命令
3. slave收到快照文件后载入数据
4. master快照发送完成后想slave发送缓冲去的写命令，slave接收命令并执行，完成复制初始化
5. 此后每次执行一个写命令都会同步发送给slave，保持master于slave之间的数据一致性

#### 特点
最简单的一种集群方案，本质上写入还是单实例（Master节点），读可以在主节点或从节点，能够实现读写分离。缺点是容量依赖单节点，无法实现分区，不具备自动容错与恢复。

## 哨兵模式
为了解决主从复制模式不能自动进行故障恢复的不足，引入特殊的哨兵节点（Sentinel），用来监控Redis节点，在发生故障时选举出领头哨兵，由领头哨兵从所有的Slave节点中选一个作为新的Master节点，完成故障转移。

#### 基本架构
![](https://upload-images.jianshu.io/upload_images/14151453-85d5f5a9c7b7a142.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

Sentinel内部互相有连接，用于监控其他Sentinel和通信，同时每个Sentinel和每个Redis节点之间有两条连接，一个连接用来发送命令通信，一个连接用来订阅Redis节点的`_sentinel_:hello`频道和获取监控该节点其他Sentinel的信息。

#### 工作原理
与Master建立连接后，Sentinel会执行以下操作：
1. 定期向Master和Slave发送INFO命令，发送INFO命令可以获取当前数据库节点信息，如果当前是Master节点，能自动发现Master的Slave节点。
2. 定期向Master和Slave的`_sentinel_:hello`频道发送自己的信息
3. 定期向Master、Slave和其他Sentinel发送PING命令

#### 故障转移
如果Sentinel向数据库节点发送的PING命令超时，Sentinel认为其主管下线，如果该节点是主节点，Sentinel会向其他Sentinel发送命令询问他们是否也认为改Master主观下线，如果达到一定数量的投票，Sentinel会认为改Master客观下线，并开启选举领头节点进行故障恢复，选举采用Raft算法：
1. 认为Master客观下线的Sentinel-1向每个Sentinel发送命令，要求对方选自己为领头哨兵。
2. 如果目标Sentinel节点没有选过其他人，则会同意选举Sentinel-1为领头哨兵
3. 如果有超过一半的Sentinel统一Sentinel-1当选领头，则Sentinel-1成为领头。
4. 如果有多个Sentinel同时竞选，导致一轮投票没有选出领头，则开启下一轮竞选，直到选出领头。

领头哨兵从故障Master的Slave节点选出一个当选新的Master，选择的规则如下：
1. 所有在线的Slave选优先级最高的，优先级通过slave-priority配置
2. 如果有多个高优先级的Slave，则选取复制偏移量最大的（数据最完整的）
3. 如果以上条件都一样，选取id最小的

挑选出要升级的Slave后，领头Sentinel向该节点发送命令使其成为Master，然后再向其他Slave发送命令接收新的Master，其他Slave收到命令后向新的Master节点发送命令进行数据同步，将故障的Master更新为新的Master的Slave节点。

#### 特点
能够自动故障转移，提高了可用性，但是同样还是存在主从复制模式的难以扩容，受限于Redis单机能力的缺点。

## Redis Cluster

#### 基本架构
![](https://upload-images.jianshu.io/upload_images/14151453-2f8e053a25c9dd4d.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

Cluster采用无中心架构
1. 所有Redis节点彼此互联，内部使用二进制协议优化传输速度和带宽
2. 节点的fail是通过集群中半数以上节点检测失效判定的
3. 客户端与key所在的Redis节点不需要直连，内部会做重定向；不需要中间代理层，客户端连接集群任意一个节点即可。

#### 工作原理
1. Redis Cluster引入了槽位slot的概念（取值0-16383），每个节点均分这些slot
2. 当对某个key操作的时候，Redis会计算key的crc16值，然后对16384取模，这样每个key都会对应一个0-16383范围的哈希槽，根据哈希槽找到负责对应槽位的节点，然后自动跳转到这个槽位上进行存取操作
3. 为了提高可用性，Cluster同时支持主从复制，每个Master对应一个或多个Slave节点，当主节点宕机的时候启动从节点
4. 如果一个集群半数以上的Master节点认为某个Master节点疑似下线，那么这个Master将被标记为已下线。

故障转移的方法和Sentinel模式类似：
1. 从复制故障Master节点的所有Slave节点选一个作为新的Master
2. 被选中的Slave节点执行`SLAVEOF no one`命令，成为新的Master节点
3. 新的Master节点会撤销所有对已下线Master节点的槽指派，将这些槽指派给自己
4. 新的Master节点向集群广播一条PONG消息，让集群中的其他节点知道这个节点已经由Slave变成了Master节点，并且已接管了槽位
5. 新的主节点开始接受和自己负责处理的slot有关的命令请求，故障转移完成。

#### 特点
##### 优点
- 无中心架构，不存在单点故障
- 不需要中间代理，减少依赖
- 支持横向扩展，伸缩性更好，能提供的并发能力更高
- 能自动故障转移，高可用

##### 缺点
- 客户端实现复杂
- 数据异步复制，不保证数据强一致性
- Slave作为冷备不提供服务
- 批量操作限制
- 事务支持有限，只支持多key在同一节点的事务操作

## 参考
【1】书籍：Redis设计与实现
【2】 [一文掌握Redis的三种集群方案](https://segmentfault.com/a/1190000022028642)
