---
title: VSCode 项目多窗口改为多 Tab 样式
slug: vscode-multi-tab
date: 2023-07-01 12:07:04
categories:
- 工具
tags:
- VSCode
---

## 环境

- macOS Ventura 13.4
- VSCode 1.79.2

## 问题

当打开多个项目时，每个项目都占一个新的窗口，日常工作经常会打开至少五个以上项目，多窗口切换不方便，个人更习惯只开一个窗口，多个项目分多个 Tab 的模式
![](vscode-multi-window.png)

## 解决方法

按如下方式可以切换到分 Tab 模式：

1. 打开 Mac 系统偏好设置，找到「桌面与程序坞」选项（低版本系统在「通用」里），将「打开文稿时首选标签页」选项改为 **始终**
![](macos-setting.png)

2. 打开 VSCode 偏好设置（快捷键 cmd + ,）
![](vscode-setting.png)

3. 搜索 native tab 结果如下，将选项设为开启状态（需要重启 VSCode）
![](vscode-setting-native-tab.png)

4. 重启后效果窗口效果变成如下样式
![](vscode-multi-tab.png)

至此即可通过开关「Native Tab」设置切换 VS Code 的窗口样式。
