FROM continuumio/miniconda3:latest

WORKDIR /app

# 设置构建参数
ARG BUILD_DATE=unknown
ARG BUILD_VERSION=latest

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 创建conda环境
RUN conda create -n app-env python=3.8 -y && \
    conda install -n app-env -c conda-forge numpy=1.21.6 pandas=1.3.5 flask=2.3.3 openpyxl=3.1.2 python-dotenv=1.0.0 requests=2.31.0 gunicorn=21.2.0 flask-cors=4.0.0 -y && \
    conda clean -afy

# 设置环境变量
ENV PATH /opt/conda/envs/app-env/bin:$PATH
ENV BUILD_DATE=${BUILD_DATE}
ENV BUILD_VERSION=${BUILD_VERSION}

# 复制应用代码
COPY . .

# 创建上传目录
RUN mkdir -p uploads && chmod 777 uploads

# 设置环境变量
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# 确保应用监听所有网络接口
ENV HOST=0.0.0.0

# 暴露容器内部端口
EXPOSE 5000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# 激活conda环境并运行应用
CMD ["conda", "run", "--no-capture-output", "-n", "app-env", "python", "app.py"] 