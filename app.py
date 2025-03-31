from flask import Flask, render_template, request, jsonify, send_from_directory
import pandas as pd
import os
from dotenv import load_dotenv
import requests

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# 确保上传文件夹存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 加载环境变量
load_dotenv()

def translate_text(text, api_config):
    """
    使用自定义API进行翻译
    """
    api_url = api_config.get('url', os.getenv('TRANSLATION_API_URL'))
    api_key = api_config.get('key', os.getenv('TRANSLATION_API_KEY'))
    prompt = api_config.get('prompt', os.getenv('TRANSLATION_PROMPT', '请将以下文本翻译成中文：'))
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "text": f"{prompt}\n{text}",
        "target_language": "zh"
    }
    
    try:
        response = requests.post(api_url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()["translated_text"]
    except Exception as e:
        return f"翻译错误: {str(e)}"

@app.route('/')
def index():
    return render_template('index.html')

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
        # 读取Excel文件
        df = pd.read_excel(file)
        
        # 确保A列存在
        if len(df.columns) == 0:
            return jsonify({"error": "Excel文件为空"}), 400
        
        # 获取API配置
        api_config = {
            'url': request.form.get('api_url'),
            'key': request.form.get('api_key'),
            'prompt': request.form.get('prompt')
        }
        
        # 翻译A列
        df['A'] = df['A'].apply(lambda x: translate_text(str(x), api_config))
        
        # 保存翻译后的文件
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], 'translated_' + file.filename)
        df.to_excel(output_path, index=False)
        
        return jsonify({
            "message": "翻译完成",
            "filename": 'translated_' + file.filename
        })
    
    except Exception as e:
        return jsonify({"error": f"处理文件时出错: {str(e)}"}), 500

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True) 