document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('uploadForm');
    const fileInput = document.getElementById('fileInput');
    const statusSection = document.getElementById('status');
    const feedbackText = document.getElementById('feedbackText');
    const submitFeedback = document.getElementById('submitFeedback');
    const apiUrlInput = document.getElementById('apiUrl');
    const apiKeyInput = document.getElementById('apiKey');
    const promptInput = document.getElementById('prompt');
    const saveConfigBtn = document.getElementById('saveConfig');

    // 从localStorage加载保存的API配置
    const savedApiUrl = localStorage.getItem('apiUrl');
    const savedApiKey = localStorage.getItem('apiKey');
    const savedPrompt = localStorage.getItem('prompt');

    if (savedApiUrl) apiUrlInput.value = savedApiUrl;
    if (savedApiKey) apiKeyInput.value = savedApiKey;
    if (savedPrompt) promptInput.value = savedPrompt;

    // 保存API配置
    saveConfigBtn.addEventListener('click', async function() {
        const config = {
            url: apiUrlInput.value.trim(),
            key: apiKeyInput.value.trim(),
            prompt: promptInput.value.trim()
        };

        try {
            const response = await fetch('/api/config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(config)
            });

            const data = await response.json();

            if (response.ok) {
                showStatus('API配置已保存', 'success');
            } else {
                showStatus(data.error || '保存配置失败', 'error');
            }
        } catch (error) {
            showStatus('保存配置时出错：' + error.message, 'error');
        }
    });

    uploadForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const file = fileInput.files[0];
        if (!file) {
            showStatus('请选择一个文件', 'error');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        try {
            showStatus('正在上传并翻译文件...', 'info');
            
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (response.ok) {
                showStatus('翻译完成！', 'success');
                // 创建下载链接
                const downloadLink = document.createElement('a');
                downloadLink.href = `/download/${data.filename}`;
                downloadLink.textContent = '下载翻译后的文件';
                downloadLink.className = 'submit-btn';
                statusSection.appendChild(downloadLink);
            } else {
                showStatus(data.error || '上传失败', 'error');
            }
        } catch (error) {
            showStatus('发生错误：' + error.message, 'error');
        }
    });

    submitFeedback.addEventListener('click', async function() {
        const feedback = feedbackText.value.trim();
        if (!feedback) {
            showStatus('请输入反馈内容', 'error');
            return;
        }

        try {
            // 这里可以添加发送反馈到后端的代码
            showStatus('感谢您的反馈！', 'success');
            feedbackText.value = '';
        } catch (error) {
            showStatus('提交反馈失败：' + error.message, 'error');
        }
    });

    function showStatus(message, type) {
        statusSection.textContent = message;
        statusSection.className = 'status-section ' + type;
    }
}); 