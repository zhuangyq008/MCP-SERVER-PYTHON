# 将代码添加到GitHub的步骤

以下是将此代码库添加到GitHub的详细步骤：

## 1. 安装Git（如果尚未安装）

```bash
# 在Ubuntu/Debian上
sudo apt-get update
sudo apt-get install git

# 在CentOS/RHEL上
sudo yum install git

# 在macOS上（使用Homebrew）
brew install git

# 在Windows上
# 下载并安装Git：https://git-scm.com/download/win
```

## 2. 配置Git

```bash
git config --global user.name "你的GitHub用户名"
git config --global user.email "你的GitHub邮箱"
```

## 3. 初始化本地Git仓库

在项目根目录下执行：

```bash
cd /path/to/your/project
git init
```

## 4. 添加文件到暂存区

```bash
# 添加所有文件
git add .

# 或者选择性地添加文件
# git add README.md
# git add weather/
# git add mcp-demo-s3table-qry/
```

## 5. 提交更改

```bash
git commit -m "初始提交"
```

## 6. 在GitHub上创建新仓库

1. 登录GitHub账户
2. 点击右上角的"+"图标，选择"New repository"
3. 填写仓库名称
4. 可以选择添加描述（可选）
5. 选择仓库可见性（公开或私有）
6. 不要初始化仓库（不要添加README、.gitignore或许可证）
7. 点击"Create repository"

## 7. 将本地仓库与GitHub仓库关联

```bash
git remote add origin https://github.com/你的用户名/你的仓库名.git
```

## 8. 推送代码到GitHub

```bash
# 推送到主分支
git push -u origin main

# 如果你的默认分支是master而不是main，则使用：
# git push -u origin master
```

## 9. 验证

访问你的GitHub仓库链接，确认代码已成功上传。

## 注意事项

- 我们已经创建了一个`.gitignore`文件，它会自动排除不需要提交到GitHub的文件。
- 确保不要将敏感信息（如API密钥、密码等）提交到GitHub。
- 如果你需要处理大文件，可能需要考虑使用Git LFS。

## 后续操作

每次修改代码后，可以使用以下命令更新GitHub仓库：

```bash
git add .
git commit -m "描述你的更改"
git push
```