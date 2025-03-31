# Excel翻译工具

这是一个基于Web的Excel翻译工具，可以将Excel文件中的A列内容自动翻译成中文。支持自定义翻译API和提示词，并提供Docker部署支持。

## 功能特点

- 支持上传Excel文件（.xlsx, .xls格式）
- 自动翻译A列内容
- 支持自定义翻译API和提示词
- 提供翻译反馈功能
- 支持Docker部署
- 支持GitHub Actions自动构建和部署

## 技术栈

- 后端：Python Flask
- 前端：HTML, CSS, JavaScript
- 数据处理：pandas
- 部署：Docker, Docker Compose
- CI/CD：GitHub Actions

## 快速开始

### 本地开发环境

1. 克隆项目：
```bash
git clone https://github.com/justincnn/excel-translator.git
cd excel-translator
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 配置环境变量：
```bash
cp .env.example .env
# 编辑.env文件，填入您的API配置
```

4. 运行应用：
```bash
python app.py
```

### Docker部署

1. 构建镜像：
```bash
docker build -t excel-translator .
```

2. 运行容器：
```bash
docker run -p 5000:5000 -v $(pwd)/uploads:/app/uploads excel-translator
```

### 使用Docker Compose部署

1. 配置环境变量：
```bash
cp .env.example .env
# 编辑.env文件，填入您的API配置
```

2. 启动服务：
```bash
docker-compose up -d
```

3. 查看服务状态：
```bash
docker-compose ps
```

4. 查看日志：
```bash
docker-compose logs -f
```

## GitHub Actions自动部署

### 配置GitHub Secrets

在GitHub仓库的Settings > Secrets and variables > Actions中添加以下secrets：

- `DOCKERHUB_USERNAME`: Docker Hub用户名
- `DOCKERHUB_TOKEN`: Docker Hub访问令牌

### 获取Docker Hub访问令牌

1. 登录 [Docker Hub](https://hub.docker.com)
2. 进入 Account Settings > Security
3. 点击 "New Access Token"
4. 设置令牌名称和权限（至少需要Read & Write）
5. 生成并复制令牌

### 自动部署流程

1. 推送代码到main分支
2. GitHub Actions自动触发构建
3. 构建Docker镜像
4. 推送镜像到Docker Hub

## 环境变量配置

在`.env`文件中配置以下变量：

```env
# API配置
TRANSLATION_API_URL=您的API地址
TRANSLATION_API_KEY=您的API密钥
TRANSLATION_PROMPT=您的翻译提示词

# Docker配置（可选）
DOCKER_IMAGE=excel-translator:latest
```

## 使用说明

1. 访问应用：打开浏览器访问 http://localhost:5000
2. 配置API信息：
   - 输入API地址
   - 输入API密钥
   - 设置翻译提示词
3. 上传Excel文件：
   - 点击"选择Excel文件"按钮
   - 选择要翻译的Excel文件
4. 开始翻译：
   - 点击"开始翻译"按钮
   - 等待翻译完成
5. 下载结果：
   - 翻译完成后点击"下载翻译后的文件"
6. 提供反馈：
   - 在反馈区域输入您的建议
   - 点击"提交反馈"按钮

## 注意事项

- 上传的Excel文件大小限制为16MB
- 确保Excel文件包含A列内容
- 翻译API需要支持JSON格式的请求和响应
- 建议定期备份uploads目录中的文件
- 确保Docker Hub账户有足够的存储空间

## 故障排除

### Docker部署问题

1. 检查Docker服务状态：
```bash
docker info
```

2. 检查容器日志：
```bash
docker-compose logs -f
```

3. 检查容器健康状态：
```bash
docker-compose ps
```

### GitHub Actions问题

1. 检查Actions日志：
   - 在GitHub仓库的Actions标签页查看详细日志
   - 确保所有secrets配置正确

2. 验证Docker Hub凭据：
```bash
docker login -u YOUR_DOCKERHUB_USERNAME -p YOUR_DOCKERHUB_TOKEN
```

## 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情 