from flask import Flask, render_template, request, jsonify, send_from_directory, session
import pandas as pd
import os
from dotenv import load_dotenv
import requests
import logging
from logging.handlers import RotatingFileHandler
import json
from flask_cors import CORS
import sqlite3
from datetime import datetime

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

# 获取构建信息
BUILD_DATE = os.getenv('BUILD_DATE', 'dev')
BUILD_VERSION = os.getenv('BUILD_VERSION', 'dev')

# 数据库配置
DB_PATH = os.getenv('DB_PATH', 'excel_translator.db')

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)  # 启用CORS

# 基础配置
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 16777216))  # 默认16MB
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev')
app.config['DEBUG'] = os.getenv('DEBUG', 'false').lower() == 'true'

# 确保上传文件夹存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# API配置文件路径
API_CONFIG_FILE = 'api_config.json'

# 初始化数据库
def init_db():
    """初始化数据库"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 创建配置表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS config (
            id INTEGER PRIMARY KEY,
            key TEXT NOT NULL,
            value TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 创建翻译历史表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS translation_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT NOT NULL,
            original_text TEXT,
            translated_text TEXT,
            translation_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            model TEXT,
            success BOOLEAN
        )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("数据库初始化成功")
    except Exception as e:
        logger.error(f"数据库初始化失败: {str(e)}")

# 获取数据库连接
def get_db_connection():
    """获取SQLite数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def db_load_api_config():
    """从数据库加载API配置"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 查询所有配置项
        cursor.execute("SELECT key, value FROM config WHERE key IN ('api_url', 'api_key', 'prompt', 'model')")
        configs = {row['key']: row['value'] for row in cursor.fetchall()}
        
        conn.close()
        
        # 构建配置对象
        return {
            'url': configs.get('api_url', os.getenv('TRANSLATION_API_URL', '')),
            'key': configs.get('api_key', os.getenv('TRANSLATION_API_KEY', '')),
            'prompt': configs.get('prompt', os.getenv('TRANSLATION_PROMPT', '请将以下文本翻译成中文，保持专业性和准确性：')),
            'model': configs.get('model', os.getenv('TRANSLATION_MODEL', ''))
        }
    except Exception as e:
        logger.error(f"从数据库加载配置失败: {str(e)}")
        # 如果从数据库加载失败，则从环境变量或文件加载
        return load_api_config()

def db_save_api_config(config):
    """保存API配置到数据库"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 将配置保存到数据库
        configs = {
            'api_url': config.get('url', ''),
            'api_key': config.get('key', ''),
            'prompt': config.get('prompt', ''),
            'model': config.get('model', '')
        }
        
        for key, value in configs.items():
            # 使用UPSERT语法，如果存在则更新，不存在则插入
            cursor.execute(
                "INSERT INTO config (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP) "
                "ON CONFLICT(key) DO UPDATE SET value = ?, updated_at = CURRENT_TIMESTAMP",
                (key, value, value)
            )
        
        conn.commit()
        conn.close()
        
        # 同时也保存到JSON文件作为备份
        save_api_config(config)
        
        return True
    except Exception as e:
        logger.error(f"保存配置到数据库失败: {str(e)}")
        # 如果保存到数据库失败，则尝试保存到文件
        return save_api_config(config)

def record_translation(file_name, original_text, translated_text, model=None, success=True):
    """记录翻译历史"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO translation_history (file_name, original_text, translated_text, model, success, translation_time) "
            "VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)",
            (file_name, original_text, translated_text, model, success)
        )
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"记录翻译历史失败: {str(e)}")
        return False

def load_api_config():
    """加载API配置（从文件）"""
    if os.path.exists(API_CONFIG_FILE):
        try:
            with open(API_CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载API配置失败: {str(e)}")
    return {
        'url': os.getenv('TRANSLATION_API_URL', ''),
        'key': os.getenv('TRANSLATION_API_KEY', ''),
        'prompt': os.getenv('TRANSLATION_PROMPT', '请将以下文本翻译成中文，保持专业性和准确性：'),
        'model': os.getenv('TRANSLATION_MODEL', '')
    }

def save_api_config(config):
    """保存API配置（到文件）"""
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
    model = api_config.get('model', '')
    
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
    
    # 如果指定了模型，则添加到请求数据中
    if model:
        data["model"] = model
    
    try:
        logger.info(f"正在翻译文本: {text[:50]}...")
        response = requests.post(api_url, headers=headers, json=data)
        response.raise_for_status()
        translated_text = response.json()["translated_text"]
        logger.info("翻译成功")
        
        # 记录成功的翻译
        record_translation(
            file_name="API请求",
            original_text=text[:500] + ('...' if len(text) > 500 else ''),
            translated_text=translated_text[:500] + ('...' if len(translated_text) > 500 else ''),
            model=model,
            success=True
        )
        
        return translated_text
    except Exception as e:
        logger.error(f"翻译错误: {str(e)}")
        
        # 记录失败的翻译
        record_translation(
            file_name="API请求",
            original_text=text[:500] + ('...' if len(text) > 500 else ''),
            translated_text=f"错误: {str(e)}",
            model=model,
            success=False
        )
        
        return f"翻译错误: {str(e)}"

# 替换被移除的before_first_request
# 初始化数据库
with app.app_context():
    init_db()
    logger.info("应用启动时初始化数据库")

@app.route('/favicon.ico')
def favicon():
    return app.send_static_file('favicon.ico')

@app.before_request
def before_request():
    """在请求前执行的操作"""
    # 添加构建信息到环境变量中，以便在模板中使用
    request.environ['BUILD_DATE'] = BUILD_DATE
    request.environ['BUILD_VERSION'] = BUILD_VERSION

@app.route('/')
def index():
    try:
        api_config = db_load_api_config()
        logger.info("成功加载首页")
        logger.info(f"构建时间: {BUILD_DATE}, 版本: {BUILD_VERSION}")
        return render_template('index.html', api_config=api_config)
    except Exception as e:
        logger.error(f"加载首页失败: {str(e)}")
        return "加载页面失败", 500

@app.route('/api/config', methods=['GET'])
def get_api_config():
    """获取API配置"""
    try:
        config = db_load_api_config()
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
        if db_save_api_config(config):
            logger.info("成功更新API配置")
            return jsonify({"message": "配置已更新"})
        return jsonify({"error": "保存配置失败"}), 500
    except Exception as e:
        logger.error(f"更新API配置失败: {str(e)}")
        return jsonify({"error": "更新配置失败"}), 500

@app.route('/api/models')
def get_models():
    """获取可用的AI模型列表"""
    try:
        api_config = load_api_config()
        if not api_config.get('url') or not api_config.get('key'):
            return jsonify({
                'success': False,
                'message': '请先配置API URL和密钥'
            }), 400

        # 构建请求URL
        models_url = f"{api_config['url'].rstrip('/')}/v1/models"
        logger.info(f"请求模型列表: {models_url}")
        
        # 发送请求获取模型列表
        response = requests.get(
            models_url,
            headers={
                'Authorization': f'Bearer {api_config["key"]}',
                'Content-Type': 'application/json'
            },
            timeout=10
        )
        
        # 检查响应状态
        if response.status_code == 200:
            models_data = response.json()
            logger.info(f"成功获取模型列表: {models_data}")
            return jsonify({
                'success': True,
                'models': models_data.get('data', [])
            })
        else:
            error_msg = f"获取模型列表失败: {response.status_code} - {response.text}"
            logger.error(error_msg)
            return jsonify({
                'success': False,
                'message': error_msg
            }), response.status_code
            
    except requests.exceptions.RequestException as e:
        error_msg = f"请求模型列表时发生错误: {str(e)}"
        logger.error(error_msg)
        return jsonify({
            'success': False,
            'message': error_msg
        }), 500
    except Exception as e:
        error_msg = f"获取模型列表时发生错误: {str(e)}"
        logger.error(error_msg)
        return jsonify({
            'success': False,
            'message': error_msg
        }), 500

@app.route('/api/history', methods=['GET'])
def get_translation_history():
    """获取翻译历史"""
    try:
        limit = int(request.args.get('limit', 20))
        offset = int(request.args.get('offset', 0))
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取历史记录总数
        cursor.execute("SELECT COUNT(*) as count FROM translation_history")
        count = cursor.fetchone()['count']
        
        # 获取分页后的历史记录
        cursor.execute(
            "SELECT id, file_name, original_text, translated_text, translation_time, model, success "
            "FROM translation_history ORDER BY translation_time DESC LIMIT ? OFFSET ?",
            (limit, offset)
        )
        history = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            "total": count,
            "history": history
        })
    except Exception as e:
        logger.error(f"获取翻译历史失败: {str(e)}")
        return jsonify({"error": f"获取翻译历史失败: {str(e)}"}), 500

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
        
        # 确保文件非空
        if df.empty:
            return jsonify({"error": "Excel文件为空"}), 400
        
        # 获取API配置
        api_config = db_load_api_config()
        model = api_config.get('model', '')
        
        # 翻译结果列
        translated_column = '翻译结果'
        success_count = 0
        error_count = 0
        
        # 如果没有'A'列，尝试使用第一列
        if 'A' not in df.columns:
            if len(df.columns) > 0:
                first_col = df.columns[0]
                logger.info(f"文件中没有'A'列，将使用第一列 '{first_col}' 进行翻译")
                
                # 遍历每一行进行翻译
                for idx, row in df.iterrows():
                    original_text = str(row[first_col]) if pd.notna(row[first_col]) else ""
                    translated_text = translate_text(original_text, api_config)
                    
                    # 检查是否翻译成功
                    if not translated_text.startswith("翻译错误:"):
                        success_count += 1
                        df.at[idx, translated_column] = translated_text
                    else:
                        error_count += 1
                        df.at[idx, translated_column] = translated_text
                        
                        # 记录翻译错误
                        record_translation(
                            file_name=file.filename,
                            original_text=original_text,
                            translated_text=translated_text,
                            model=model,
                            success=False
                        )
            else:
                return jsonify({"error": "Excel文件没有可翻译的列"}), 400
        else:
            # 如果有'A'列
            for idx, row in df.iterrows():
                original_text = str(row['A']) if pd.notna(row['A']) else ""
                translated_text = translate_text(original_text, api_config)
                
                # 检查是否翻译成功
                if not translated_text.startswith("翻译错误:"):
                    success_count += 1
                    df.at[idx, translated_column] = translated_text
                else:
                    error_count += 1
                    df.at[idx, translated_column] = translated_text
                    
                    # 记录翻译错误
                    record_translation(
                        file_name=file.filename,
                        original_text=original_text,
                        translated_text=translated_text,
                        model=model,
                        success=False
                    )
        
        # 保存翻译后的文件
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], 'translated_' + file.filename)
        df.to_excel(output_path, index=False)
        logger.info(f"文件处理完成: {output_path}, 成功: {success_count}, 失败: {error_count}")
        
        return jsonify({
            "message": f"翻译完成，共 {success_count} 条成功，{error_count} 条失败",
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

@app.route('/health')
def health_check():
    """健康检查端点"""
    return jsonify({
        "status": "ok",
        "version": BUILD_VERSION,
        "build_date": BUILD_DATE,
        "uptime": "服务正常运行"
    })

@app.route('/diagnostics')
def diagnostics():
    """诊断信息端点"""
    config = db_load_api_config()
    # 隐藏API密钥
    if 'key' in config:
        config['key'] = '***' if config['key'] else ''
    
    # 检查数据库状态
    db_status = "未初始化"
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM sqlite_master")
        tables_count = cursor.fetchone()['count']
        db_status = f"正常 ({tables_count} 个表)"
        conn.close()
    except Exception as e:
        db_status = f"错误: {str(e)}"
    
    diag_info = {
        "status": "ok",
        "version": BUILD_VERSION,
        "build_date": BUILD_DATE,
        "python_version": os.sys.version,
        "database": {
            "path": DB_PATH,
            "status": db_status
        },
        "api_config": config,
        "env_vars": {
            "FLASK_ENV": os.getenv('FLASK_ENV', 'not set'),
            "DEBUG": app.config['DEBUG'],
            "MAX_CONTENT_LENGTH": app.config['MAX_CONTENT_LENGTH'],
            "UPLOAD_FOLDER": app.config['UPLOAD_FOLDER'],
            "UPLOAD_FOLDER_EXISTS": os.path.exists(app.config['UPLOAD_FOLDER']),
            "STATIC_FOLDER": app.static_folder,
            "STATIC_FOLDER_EXISTS": os.path.exists(app.static_folder) if app.static_folder else False,
            "TEMPLATE_FOLDER": app.template_folder,
            "TEMPLATE_FOLDER_EXISTS": os.path.exists(app.template_folder) if app.template_folder else False
        }
    }
    return jsonify(diag_info)

@app.after_request
def add_header(response):
    """添加必要的响应头"""
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

if __name__ == '__main__':
    try:
        # 确保数据库初始化
        # init_db()  # 移除这行，因为我们已经在app.app_context()中初始化了
        
        host = '0.0.0.0'  # 始终监听所有网络接口
        port = int(os.getenv('PORT', 5000))  # 默认使用5000端口与Docker配置匹配
        logger.info(f"启动服务器: {host}:{port}")
        app.run(host=host, port=port, debug=app.config['DEBUG'])
    except Exception as e:
        logger.error(f"服务器启动失败: {str(e)}") 