document.addEventListener('DOMContentLoaded', function() {
    // 基础元素
    const uploadForm = document.getElementById('uploadForm');
    const fileInput = document.getElementById('fileInput');
    const statusSection = document.getElementById('status');
    const feedbackText = document.getElementById('feedbackText');
    const submitFeedback = document.getElementById('submitFeedback');
    
    // API配置元素
    const apiUrlInput = document.getElementById('apiUrl');
    const apiKeyInput = document.getElementById('apiKey');
    const promptInput = document.getElementById('prompt');
    const modelSelect = document.getElementById('model');
    const refreshModelsBtn = document.getElementById('refreshModels');
    const saveConfigBtn = document.getElementById('saveConfig');
    
    // 标签页元素
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    
    // 历史记录元素
    const historyTableBody = document.getElementById('historyTableBody');
    const refreshHistoryBtn = document.getElementById('refreshHistory');
    const prevPageBtn = document.getElementById('prevPage');
    const nextPageBtn = document.getElementById('nextPage');
    const currentPageSpan = document.getElementById('currentPage');
    const totalPagesSpan = document.getElementById('totalPages');
    
    // 历史记录状态
    let currentPage = 1;
    let totalPages = 1;
    let pageSize = 10;

    // 从localStorage加载保存的API配置
    const savedApiUrl = localStorage.getItem('apiUrl');
    const savedApiKey = localStorage.getItem('apiKey');
    const savedPrompt = localStorage.getItem('prompt');
    const savedModel = localStorage.getItem('model');

    if (savedApiUrl) apiUrlInput.value = savedApiUrl;
    if (savedApiKey) apiKeyInput.value = savedApiKey;
    if (savedPrompt) promptInput.value = savedPrompt;
    if (savedModel && !modelSelect.querySelector(`option[value="${savedModel}"]`)) {
        const option = document.createElement('option');
        option.value = savedModel;
        option.textContent = savedModel;
        option.selected = true;
        modelSelect.appendChild(option);
    }

    // 标签页切换
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabName = button.dataset.tab;
            
            // 激活按钮
            tabButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            
            // 显示对应内容
            tabContents.forEach(content => {
                content.classList.remove('active');
                if (content.id === `${tabName}-tab`) {
                    content.classList.add('active');
                    
                    // 如果切换到历史记录标签，自动加载历史记录
                    if (tabName === 'history') {
                        loadTranslationHistory();
                    }
                }
            });
        });
    });

    // 保存API配置
    saveConfigBtn.addEventListener('click', async function() {
        const config = {
            url: apiUrlInput.value.trim(),
            key: apiKeyInput.value.trim(),
            prompt: promptInput.value.trim(),
            model: modelSelect.value
        };

        // 保存到localStorage
        localStorage.setItem('apiUrl', config.url);
        localStorage.setItem('apiKey', config.key);
        localStorage.setItem('prompt', config.prompt);
        localStorage.setItem('model', config.model);

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
            console.error('保存配置时出错：', error);
        }
    });

    // 获取模型列表
    refreshModelsBtn.addEventListener('click', async function() {
        if (!apiUrlInput.value || !apiKeyInput.value) {
            showStatus('请先填写API URL和密钥', 'error');
            return;
        }

        try {
            refreshModelsBtn.classList.add('loading');
            showStatus('正在获取模型列表...', 'info');

            const response = await fetch('/api/models');
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || '获取模型列表失败');
            }

            const data = await response.json();
            
            // 清除当前选项并保留默认选项
            while (modelSelect.options.length > 1) {
                modelSelect.remove(1);
            }
            
            // 添加新选项
            data.models.forEach(model => {
                const option = document.createElement('option');
                option.value = model.id;
                option.textContent = model.id.split(':').pop() || model.id;
                
                // 如果与保存的值匹配，则选中
                if (model.id === localStorage.getItem('model')) {
                    option.selected = true;
                }
                
                modelSelect.appendChild(option);
            });
            
            showStatus(`已加载 ${data.models.length} 个模型`, 'success');
        } catch (error) {
            showStatus('获取模型失败：' + error.message, 'error');
            console.error('获取模型失败：', error);
        } finally {
            refreshModelsBtn.classList.remove('loading');
        }
    });

    // 文件上传和翻译
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
                showStatus(data.message || '翻译完成！', 'success');
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
            console.error('上传文件时出错：', error);
        }
    });

    // 提交反馈
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
            console.error('提交反馈失败：', error);
        }
    });

    // 加载翻译历史
    async function loadTranslationHistory() {
        try {
            const offset = (currentPage - 1) * pageSize;
            
            refreshHistoryBtn.classList.add('loading');
            historyTableBody.innerHTML = '<tr><td colspan="7" class="text-center">加载中...</td></tr>';
            
            const response = await fetch(`/api/history?limit=${pageSize}&offset=${offset}`);
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || '获取历史记录失败');
            }
            
            const data = await response.json();
            
            // 清空表格
            historyTableBody.innerHTML = '';
            
            // 如果没有记录
            if (data.history.length === 0) {
                historyTableBody.innerHTML = '<tr><td colspan="7" class="text-center">暂无记录</td></tr>';
                return;
            }
            
            // 计算总页数
            totalPages = Math.ceil(data.total / pageSize);
            totalPagesSpan.textContent = totalPages;
            currentPageSpan.textContent = currentPage;
            
            // 更新翻译历史表格
            data.history.forEach(record => {
                const row = document.createElement('tr');
                
                const idCell = document.createElement('td');
                idCell.textContent = record.id;
                row.appendChild(idCell);
                
                const fileNameCell = document.createElement('td');
                fileNameCell.textContent = record.file_name;
                row.appendChild(fileNameCell);
                
                const originalTextCell = document.createElement('td');
                const originalTextSpan = document.createElement('span');
                originalTextSpan.className = 'text-truncate';
                originalTextSpan.title = record.original_text;
                originalTextSpan.textContent = record.original_text;
                originalTextCell.appendChild(originalTextSpan);
                row.appendChild(originalTextCell);
                
                const translatedTextCell = document.createElement('td');
                const translatedTextSpan = document.createElement('span');
                translatedTextSpan.className = 'text-truncate';
                translatedTextSpan.title = record.translated_text;
                translatedTextSpan.textContent = record.translated_text;
                translatedTextCell.appendChild(translatedTextSpan);
                row.appendChild(translatedTextCell);
                
                const timeCell = document.createElement('td');
                const date = new Date(record.translation_time);
                timeCell.textContent = date.toLocaleString();
                row.appendChild(timeCell);
                
                const modelCell = document.createElement('td');
                modelCell.textContent = record.model || '-';
                row.appendChild(modelCell);
                
                const statusCell = document.createElement('td');
                statusCell.textContent = record.success ? '成功' : '失败';
                statusCell.className = record.success ? 'success' : 'error';
                row.appendChild(statusCell);
                
                historyTableBody.appendChild(row);
            });
            
            // 更新分页按钮状态
            prevPageBtn.disabled = currentPage <= 1;
            nextPageBtn.disabled = currentPage >= totalPages;
            
        } catch (error) {
            historyTableBody.innerHTML = `<tr><td colspan="7" class="text-center error">加载失败: ${error.message}</td></tr>`;
            console.error('加载历史记录失败：', error);
        } finally {
            refreshHistoryBtn.classList.remove('loading');
        }
    }
    
    // 刷新历史记录
    refreshHistoryBtn.addEventListener('click', () => {
        loadTranslationHistory();
    });
    
    // 上一页
    prevPageBtn.addEventListener('click', () => {
        if (currentPage > 1) {
            currentPage--;
            loadTranslationHistory();
        }
    });
    
    // 下一页
    nextPageBtn.addEventListener('click', () => {
        if (currentPage < totalPages) {
            currentPage++;
            loadTranslationHistory();
        }
    });

    // 显示状态信息
    function showStatus(message, type) {
        statusSection.textContent = message;
        statusSection.className = 'status-section ' + type;
    }
}); 