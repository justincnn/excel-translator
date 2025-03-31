from flask import Flask, render_template, request, jsonify, send_from_directory, session
import pandas as pd
import os
from dotenv import load_dotenv
import requests
import logging
from logging.handlers import RotatingFileHandler
import json

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('app.log', maxBytes=1024*1024, backupCount=5),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# 基础配置
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 16)) * 1024 * 1024  # 转换为字节
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev')
app.config['DEBUG'] = os.getenv('DEBUG', 'false').lower() == 'true'

# 确保上传文件夹存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# API配置文件路径
API_CONFIG_FILE = 'api_config.json'

def load_api_config():
    """加载API配置"""
    if os.path.exists(API_CONFIG_FILE):
        try:
            with open(API_CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载API配置失败: {str(e)}")
    return {
        'url': os.getenv('TRANSLATION_API_URL', ''),
        'key': os.getenv('TRANSLATION_API_KEY', ''),
        'prompt': os.getenv('TRANSLATION_PROMPT', '请将以下文本翻译成中文，保持专业性和准确性：')
    }

def save_api_config(config):
    """保存API配置"""
    try:
        with open(API_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"保存API配置失败: {str(e)}")
        return False

def translate_text(text, api_config):
    """
    使用自定义API进行翻译
    """
    api_url = api_config.get('url')
    api_key = api_config.get('key')
    prompt = api_config.get('prompt')
    
    if not api_url or not api_key:
        return "错误：请先配置API信息"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "text": f"{prompt}\n{text}",
        "target_language": "zh"
    }
    
    try:
        logger.info(f"正在翻译文本: {text[:50]}...")
        response = requests.post(api_url, headers=headers, json=data)
        response.raise_for_status()
        translated_text = response.json()["translated_text"]
        logger.info("翻译成功")
        return translated_text
    except Exception as e:
        logger.error(f"翻译错误: {str(e)}")
        return f"翻译错误: {str(e)}"

@app.route('/')
def index():
    try:
        api_config = load_api_config()
        logger.info("成功加载首页")
        return render_template('index.html', api_config=api_config)
    except Exception as e:
        logger.error(f"加载首页失败: {str(e)}")
        return "加载页面失败", 500

@app.route('/api/config', methods=['GET'])
def get_api_config():
    """获取API配置"""
    try:
        config = load_api_config()
        logger.info("成功获取API配置")
        return jsonify(config)
    except Exception as e:
        logger.error(f"获取API配置失败: {str(e)}")
        return jsonify({"error": "获取配置失败"}), 500

@app.route('/api/config', methods=['POST'])
def update_api_config():
    """更新API配置"""
    try:
        config = request.json
        if save_api_config(config):
            logger.info("成功更新API配置")
            return jsonify({"message": "配置已更新"})
        return jsonify({"error": "保存配置失败"}), 500
    except Exception as e:
        logger.error(f"更新API配置失败: {str(e)}")
        return jsonify({"error": "更新配置失败"}), 500

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "没有文件被上传"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "没有选择文件"}), 400
    
    if not file.filename.endswith(('.xlsx', '.xls')):
        return jsonify({"error": "只支持Excel文件"}), 400
    
    try:
        logger.info(f"开始处理文件: {file.filename}")
        # 读取Excel文件
        df = pd.read_excel(file)
        
        # 确保A列存在
        if len(df.columns) == 0:
            return jsonify({"error": "Excel文件为空"}), 400
        
        # 获取API配置
        api_config = load_api_config()
        
        # 翻译A列
        df['A'] = df['A'].apply(lambda x: translate_text(str(x), api_config))
        
        # 保存翻译后的文件
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], 'translated_' + file.filename)
        df.to_excel(output_path, index=False)
        logger.info(f"文件处理完成: {output_path}")
        
        return jsonify({
            "message": "翻译完成",
            "filename": 'translated_' + file.filename
        })
    
    except Exception as e:
        logger.error(f"处理文件时出错: {str(e)}")
        return jsonify({"error": f"处理文件时出错: {str(e)}"}), 500

@app.route('/download/<filename>')
def download_file(filename):
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)
    except Exception as e:
        logger.error(f"下载文件失败: {str(e)}")
        return "下载文件失败", 500

if __name__ == '__main__':
    try:
        host = os.getenv('HOST', '0.0.0.0')
        port = int(os.getenv('PORT', 6763))
        logger.info(f"启动服务器: {host}:{port}")
        app.run(host=host, port=port, debug=app.config['DEBUG'])
    except Exception as e:
        logger.error(f"服务器启动失败: {str(e)}") 