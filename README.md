# Excel翻译工具

这是一个基于Web的Excel翻译工具，可以将Excel文件中的A列内容自动翻译成中文。

## 功能特点

- 支持上传Excel文件（.xlsx, .xls格式）
- 自动翻译A列内容
- 支持自定义翻译API和提示词
- 提供翻译反馈功能
- 支持Docker部署

## 部署说明

### 使用Docker Compose部署

1. 克隆项目到本地：
```bash
git clone <repository_url>
cd excel-translator
```

2. 复制环境变量配置文件：
```bash
cp .env.example .env
```

3. 编辑.env文件，配置您的API信息：
```
TRANSLATION_API_URL=您的API地址
TRANSLATION_API_KEY=您的API密钥
TRANSLATION_PROMPT=您的翻译提示词
```

4. 使用Docker Compose启动应用：
```bash
docker-compose up -d
```

5. 访问应用：
打开浏览器访问 http://localhost:5000

### 手动部署

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 配置环境变量：
```bash
cp .env.example .env
# 编辑.env文件，填入您的API配置
```

3. 运行应用：
```bash
python app.py
```

## 使用说明

1. 在Web界面上配置您的翻译API信息（URL、密钥和提示词）
2. 点击"选择Excel文件"按钮上传您的Excel文件
3. 点击"开始翻译"按钮开始翻译
4. 等待翻译完成后，可以下载翻译后的文件
5. 如果翻译结果需要改进，可以在反馈区域输入您的建议

## 注意事项

- 上传的Excel文件大小限制为16MB
- 确保Excel文件包含A列内容
- 翻译API需要支持JSON格式的请求和响应
- 建议定期备份uploads目录中的文件

## 技术栈

- 后端：Python Flask
- 前端：HTML, CSS, JavaScript
- 数据处理：pandas
- 部署：Docker, Docker Compose 