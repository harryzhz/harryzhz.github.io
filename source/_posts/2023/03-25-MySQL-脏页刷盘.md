---
title: MySQL 脏页刷盘
date: 2023-03-25 15:12:03
categories:
- [数据库]
tags:
- MySQL
- 脏页
---
## 什么是脏页？
InnoDB在处理更新语句时，先写内存再写redo log，并不会立即将数据页的更新落地到磁盘（WAL机制），这就会产生升内存数据页和磁盘数据页的数据不一致的情况，这种数据不一致的数据页称为**脏页**，当脏页写入到磁盘（这个操作称为flush）后，数据一致后称为干净页。

## 什么时候会flush脏页？
1. redo log写满
redo log大小是固定的，写完后会循环覆盖写入。当有新的内容要写入时，系统必须停止所有的更新操作，将checkpoint向前推进到新的位置，但是在推进之前必须将覆盖部分的所有脏页都flush到磁盘上。
![](https://upload-images.jianshu.io/upload_images/14151453-05061327e5e6e8fa.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

2. 内存不足需要淘汰数据页
当系统内存不足，又有新的数据页要更新，就需要淘汰一些数据页，如果淘汰的是脏页，就需要flush到磁盘（如果是干净页就直接释放出来复用）。

3. 系统空闲的时候后台会定期flush适量的脏页到磁盘
4. MySQL正常关闭（shut down）时会把所有脏页都flush到磁盘

## flush对系统性能的影响
第3种是系统空闲不会有性能问题，第4种是要关闭了不考虑性能问题。第1和2的情况flush脏页会产生系统性能问题。
### redo log写满
此时整个系统不能再更新了，更新数会降为0，所以这种情况要尽量避免。

### 内存不够
InnoDB缓冲池（buffer pool）中的内存页有三种状态：
- 未使用的空闲内存
- 使用了为脏页
- 使用了未干净页

当一个SQL语句要淘汰的脏页数量太多，会导致语句执行的响应时间显著边长。

## flush速度控制策略
InnoDB为了避免出现上述两种情况，需要有控制脏页比例的策略，控制的主要参考因素就是：脏页比例和redo log写盘速度。

#### 磁盘的IO能力
需要告诉InnoDB的磁盘读写能力（IOPS）让引擎全力flush脏页，磁盘的IOPS可以通过fio工具测试。
```shell
 fio -filename=$filename -direct=1 -iodepth 1 -thread -rw=randrw -ioengine=psync -bs=16k -size=500M -numjobs=10 -runtime=10 -group_reporting -name=mytest 
```

如果`innodb_io_capacity`参数设置的不合理，比如远远低于磁盘实际的IOPS，InnoDB会认为IO性能低，刷脏页速度会很慢，甚至低于脏页的生成速度，导致脏页累计影响查询和更新性能。

#### 速度计算流程
为了兼顾正常的业务请求，InnoDB引擎控制按照磁盘IOPS的百分比来刷脏页，具体流程如下：
1. 参数`innodb_max_dirty_pages_pct`控制脏页比例上限，默认75%。InnoDB根据当前脏页比例（设为M），计算出一个0~100的数字F1(M)，伪代码如下
```python
def F1(M):
    if M >= innodb_max_dirty_pages_pct:
        return 100
    return 100 * M / innodb_max_dirty_pages_pct
```
2. InnoDB每次写入的日志都有一个序号，当前写入的序号跟checkpoint对应的需要之间的差值设为N，根据N计算出一个0~100的数值F2(N)，N越大F2(N)越大
3. 根据前两步计算出的两个值取较大值记为R，然后InnoDB会根据`innodb_io_capacity`设置的磁盘IOPS能力乘以R%来控制刷脏页的速度

脏页比例计算:
`Innodb_buffer_pool_pages_dirty/Innodb_buffer_pool_pages_total`
SQL语句如下：
```sql
select VARIABLE_VALUE into @a from global_status where VARIABLE_NAME = 'Innodb_buffer_pool_pages_dirty';
select VARIABLE_VALUE into @b from global_status where VARIABLE_NAME = 'Innodb_buffer_pool_pages_total';
select @a/@b;
```

## 连锁flush
在准备flush一个脏页时，如果相邻的数据页也是脏页，会把这个脏页一起flush，而且对这个新的脏页还可能有相邻的脏页导致连锁flush。
InnoDB使用`innodb_flush_neighbors`参数控制这个行为，值为1会产生上述连锁flush的情况，值为0则不会找相邻页。

找相邻页flush的机制虽然可以减少很多随机IO，但会增加一次flush时间，导致flush时的SQL语句执行时间变慢。

现在基本都使用的SSD这种IOPS比较高的硬盘，建议将`innodb_flush_neighbors`参数设为0，提高flush的速度。

## 总结
flush会占用IO资源影响了正在执行的SQL语句，本来正常情况下执行很快的一条语句，突然耗时大大增加，造成业务抖动。要尽量避免这种情况，需要合理的设置`innodb_io_capacity`的值，并且多关注脏页比例，不要让脏页比例经常接近75%。

## 参考资料
【极客时间】[MySQL实战45讲：第12节](https://time.geekbang.org/column/article/71806)
