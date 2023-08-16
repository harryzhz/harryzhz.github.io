#!/bin/bash

# 接收目录路径作为参数
directory=$1

# 检查目录是否存在
if [ ! -d "$directory" ]; then
  echo "目录不存在"
  exit 1
fi

cd "$directory"

# 获取当前年份
year=$(date +%Y)
  echo $year

# 循环处理每个文件
index=1
for file in ./*; do
  filename=$(basename "$file")
  echo "#${index} filename:$filename"

  # 提取月份和日期
  month=$(echo "$filename" | cut -d'-' -f1)
  day=$(echo "$filename" | cut -d'-' -f2)
  suffix=$(echo "$filename" | awk -F "${month}-${day}" '{print $2}')

  # 构建新的文件名
  new_name="${year}${month}${day}${suffix}"

  # 重命名文件
  echo "#${index} newname:$new_name"
  ((index++))
  mv "$file" "$new_name"
done