---
title: HTTPS原理详解
date: 2023-03-25 14:43:24
categories:
- [计算机网络]
tags:
- HTTPS
---

Web应用存在HTTP和HTTPS两种通信方式，HTTP默认端口80，数据以明文传输，HTTPS默认端口443，数据加密传输。

## HTTPS协议
HTTPS实际上并不是一种新的网络协议，是HTTP的基础上加了SSL层，数据的加密就是在SSL层完成的。
![](https://upload-images.jianshu.io/upload_images/14151453-4915c1ecfe442f0d.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

## 数据传输方式

### 明文传输
客户端和服务器已明文方式传输数据，没有安全性，数据再传输过程中可能被劫持和篡改
![](https://upload-images.jianshu.io/upload_images/14151453-af0efb8a2b3599db.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

### 对称加密传输
对称加密算法：双方使用同一秘钥对数据进行加解密（AES、DES）
![](https://upload-images.jianshu.io/upload_images/14151453-046d2c536baae247.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)
**特点**：
- 如果不知道秘钥，是无法解出对应的明文，但是如果所有客户端都用相同的秘钥，相当于没有加密，坏人也可以作为一个用户拿到秘钥。
- 加解密性能高

一种改进的方案是每个客户端先协商一个加密算法和秘钥，不同客户端使用不同的算法和秘钥，这就坏人即使作为一个用户也不知道别的用户的秘钥。但是这种方式协商秘钥的过程是公开明文的，坏人也有办法窃取到秘钥的，仍然存在风险。

### 非对称加密传输
非对称加密算法：加密解密采用不同的秘钥，私钥加密后的密文，所有的公钥都可以解密，公钥加密后的密文只有私钥能解密。私钥通常只有一个人有，公钥可以公开发给所有人。（常见算法：RSA）
![](https://upload-images.jianshu.io/upload_images/14151453-eefe11cf0a2b22f8.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)


**特点**：
- 只要把私钥保存在服务器，公钥发给客户端，那么客户端向服务器发送的数据就是安全的，但是服务器向客户端发送的数据坏人也可以通过公钥解密
- 加解密消耗的时间较长，传输效率会降低

### HTTPS（对称加密+非对称加密）
![](https://upload-images.jianshu.io/upload_images/14151453-9a21634026ce4d86.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

**特点**：
- 使用非对称加密传输协商一个对称加密算法和秘钥
- 使用对称加密算法对数据加密传输
- 数据双向安全，且效率较高

## CA机构和数字证书
从前面可以看到，协商阶段时候用非对称加密，客户端一开始就要持有公钥，那么客户端如何安全的获取公钥呢？
如果服务端直接将公钥发给客户端，中间可能被坏人劫持，返回一个假公钥，客户端使用假公钥进行加密后请求，坏人就可以使用假私钥解出明文，篡改内容后再使用真公钥加密后请求到服务器，这时服务器拿到的是被篡改后的数据。
![](https://upload-images.jianshu.io/upload_images/14151453-fb5c49e4b5019e80.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

数字证书和CA机构就是用来保证服务器安全的发送公钥给客户端的。
**校验过程**
1. 读取证书中的所有者，有效期等信息进行校验
2. 查找系统内置的受信任证书发布机构CA，与服务器下发的证书中的CA对比，校验是否是合法机构颁发
3. 如果找不到，浏览器报错警告证书不可信
4. 如果找到了：
- 对证书里的数字签名使用公钥解密得到明文的hash摘要
- 浏览器使用相同的hash算法计算明文的hash值，将这个值与上述计算的摘要对比验证证书的合法性。

## 总结
一个完整的HTTPS请求流程如下图所示：
![](https://upload-images.jianshu.io/upload_images/14151453-06d256f8dff32472.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

## 参考
【1】[【掘金】深入理解HTTPS工作原理](https://juejin.cn/post/6844903830916694030)
