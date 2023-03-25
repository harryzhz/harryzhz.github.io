---
title: MySQL ORDER BY 如何实现排序的?
date: 2023-03-25 15:12:42
categories:
- [数据库]
tags:
- MySQL
- 排序
---
## MySQL是如何进行排序的？
假设有一个表t结构如下图所示：
![](https://upload-images.jianshu.io/upload_images/14151453-c7aec6166a2d984f.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

id为主键，type上建有索引，那么如果要查类型为1，val最小的1000行，那么SQL语句如下：
`SELECT type, val, detail FROM t WHERE type = 1 ORDER BY val LIMIT 1000;`

### 全字段排序
对上述查询执行explain结果如下：
![](https://upload-images.jianshu.io/upload_images/14151453-b14d9da637a8123d.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

Using filesort表示需要排序，MySQL会给每个线程分配一块内存用来排序，称为sort buffer，具体的流程如下：
1. 初始化sort buffer，确定放入type，val，detail三个字段
2. 从索引type中找到第一个满足type=1条件的主键id
3. 根据id回主键索引查询type和val的值存入sort buffer中，从索引type中继续取下一个id
4. 重复3的操作直到type不满足条件
5. 对sort buffer中的数据按照val字段做快速排序
6. 按照排序结果取前1000行返回

如果sort buffer够存下所有需要排序的记录，排序在内存中完成，如果内存放不下则需要借助磁盘临时文件进行外部排序。

### rowid排序
全字段排序过程里只对原表扫描的一遍，剩下的操作都是在sort buffer 和临时文件中执行的，但是如果要查询的字段比较多，sort buffer能存的行数就很少，需要分成多个临时文件进行外部排序，性能比较差，所以在单行数大的情况下这种方式明显不合适。

MySQL的参数`max_length_for_sort_data`表示如果单行记录长度超过这个值，就认为单行太大，要换一种排序算法，排序过程中只放要排序的列和主键id，执行流程如下：
1. 初始化sort buffer，放入val，id字段
2. 从索引type中找到第一个满足type=1条件的主键id
3. 根据id回主键索引查询val的值，将val和id存入sort buffer中，从索引type中继续取下一个id
4. 重复3的操作直到type不满足条件
5. 对sort buffer中的数据按照val字段做快速排序
6. 按照排序结果依次取1000行，并按照id值回表取出type，val，detail三个字段返回

可以看到改流程与全字段排序的主要区别在于：
- 第1步放入sort buffer的字段不同，rowid排序只放入排序字段和id，全字段排序放入查询的全部字段
- 第6步，rowid排序完成后要再回主键索引查一次全部数据返回，全字段排序因为所以要返回的字段内容都在sort buffer中了所以直接返回

**说明**：结果集只是一个逻辑概念，实际上MySQL从排序后的sort buffer中依次取出id，然后到原表查询所有字段的结果不需要在服务端再消耗内存保存，是直接返回的。

### 联合索引避免排序
上面两种方法都是需要建临时表进行排序的，对于MySQL来说都是成本比较高的操作。但并不是所有order by都是需要排序的，因为MySQL索引是天然有序的，如果在type和val字段创建一个联合索引idx_type_val，那么该查询就不需要排序了，这时执行过程就变成了如下流程：
1. 在索引idx_type_val上找到第一个满足type=1条件记录
2. 根据索引上的主键id回主键索引查询所有字段的值返回，在idx_type_val索引上继续取一下个值
3. 重复2的操作直到不满足type=1或者超过1000行结束。

使用联合索引，首先不在需要建临时表做排序，其次也不需要扫描出满足type=1条件的所有记录，因为索引有序直接扫描前1000行就结束了，大大减少了扫描的行数。

## 优先队列排序

对于MySQL来说并不是所有的排序都是用快速排序实现的，假如之前的查询变成了如下：
`EXPLAIN SELECT type, val FROM t WHERE type = 1 ORDER BY val LIMIT 3;`
假设type=1的记录有1万条，只需要去前val最小的前三行。

对于这种情况，即使sort buffer不能放下1万行记录，会发现MySQL也没有使用到临时文件，这时因为选择了另一种算法：优先队列算法。

#### 算法流程
1. 对于这10000准备排序的记录，先取前三行构造一个最大堆
2. 取下一行Next记录跟当前堆顶记录Top比较，如果Next.val < Top.val，就把堆顶记录弹出，将Next记录放入堆
3. 重复2的操作直到取出所有10000行记录，最后堆中的三个记录就是最小的三个

#### 复杂度
快速排序时间复杂度是`O(N*logN)`，优先队列排序时间复杂度为`O((N-K)*logK)`，K表示堆的大小，即返回记录的个数，对于该场景下为`(N-3)*log3`，基本可以看做线性时间复杂度，如果是limit 1的时候就相当于求最小值，该算法就是线性时间复杂度。
其次sort buffer中只需要维护堆，内存的消耗也大大减少，空间复杂度为`O(K)`。

## order by rand()
如果需要随机选1个数，SQL语句可能如下：
`SELECT * FROM t ORDER BY RAND() LIMIT 1`
需要注意到是这种方式会建临时表进行排序，临时表除了查询字段会多加一个排序字段存放rand()生成的值，即对每一行记录使用rand()函数生成一个随机数，然后根据这个数来排序。

这种写法的成本是比较高的，所以建议尽量避免这种写法，建议先随机一个0~N-1的值（N表示表总行数），然后去查数据库的某行，比如：
```python
def rand1():
    N = mysql.query("select count(*) from t")
    res = mysql.query("select * from t limit N, 1")
    return res
```

## 参考
【极客时间】[MySQL实战45讲：16、17](https://time.geekbang.org/column/article/73479)
