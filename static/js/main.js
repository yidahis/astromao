    // 使用let而不是const，以便在DOMContentLoaded中重新赋值
    let fileInput, jsonInput, audioForJsonInput, uploadBtn, importBtn, selectAudioBtn,
        recognizeBtn, historyBtn, uploadSection, fileInfo, progressContainer, progressFill,
        resultsSection, errorMessage, successMessage;

    let selectedFile = null;
    let importedJsonData = null;
    let selectedAudioForJson = null;
    
    // 将秒数转换为时分秒格式
    function formatTimeToHMS(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);
        const millisecs = Math.floor((seconds % 1) * 100);
        
        if (hours > 0) {
            return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}.${millisecs.toString().padStart(2, '0')}`;
        } else {
            return `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}.${millisecs.toString().padStart(2, '0')}`;
        }
    }
    
    // 确保DOM加载完成
    document.addEventListener('DOMContentLoaded', function() {
        console.log('DOM已加载完成');
        // 在DOM加载完成后初始化所有元素引用
        fileInput = document.getElementById('fileInput');
        jsonInput = document.getElementById('jsonInput');
        audioForJsonInput = document.getElementById('audioForJsonInput');
        uploadBtn = document.getElementById('uploadBtn');
        importBtn = document.getElementById('importBtn');
        selectAudioBtn = document.getElementById('selectAudioBtn');
        recognizeBtn = document.getElementById('recognizeBtn');
        historyBtn = document.getElementById('historyBtn');
        uploadSection = document.getElementById('uploadSection');
        fileInfo = document.getElementById('fileInfo');
        progressContainer = document.getElementById('progressContainer');
        progressFill = document.getElementById('progressFill');
        resultsSection = document.getElementById('resultsSection');
        errorMessage = document.getElementById('errorMessage');
        successMessage = document.getElementById('successMessage');
        
        // 检查关键元素是否存在
        const editModeBtn = document.getElementById('editModeBtn');
        const editControlPanel = document.getElementById('editControlPanel');
        const bilingualModeBtn = document.getElementById('bilingualModeBtn');
        console.log('编辑模式按钮:', editModeBtn);
        console.log('编辑控制面板:', editControlPanel);
        console.log('双语模式按钮:', bilingualModeBtn);
        
        // 只有当元素存在时才添加事件监听器
        if (editModeBtn) {
            editModeBtn.addEventListener('click', toggleEditMode);
        }
        
        if (bilingualModeBtn) {
            bilingualModeBtn.addEventListener('click', toggleBilingualMode);
        }
        
        // File input change event
        if (fileInput) fileInput.addEventListener('change', handleFileSelect);
        if (jsonInput) jsonInput.addEventListener('change', handleJsonImport);
        if (audioForJsonInput) audioForJsonInput.addEventListener('change', handleAudioForJsonSelect);
        if (uploadBtn) uploadBtn.addEventListener('click', () => fileInput && fileInput.click());
        if (importBtn) importBtn.addEventListener('click', () => jsonInput && jsonInput.click());
        if (selectAudioBtn) selectAudioBtn.addEventListener('click', () => audioForJsonInput && audioForJsonInput.click());
        if (recognizeBtn) recognizeBtn.addEventListener('click', recognizeAudio);
        if (historyBtn) historyBtn.addEventListener('click', showResultsHistory);

        // Drag and drop events
        if (uploadSection) {
            uploadSection.addEventListener('dragover', (e) => {
                e.preventDefault();
                uploadSection.classList.add('dragover');
            });
            
            uploadSection.addEventListener('dragleave', (e) => {
                e.preventDefault();
                uploadSection.classList.remove('dragover');
            });
            
            uploadSection.addEventListener('drop', (e) => {
                e.preventDefault();
                uploadSection.classList.remove('dragover');
                if (e.dataTransfer.files.length) {
                    handleFileSelect({ target: { files: e.dataTransfer.files } });
                }
            });
        }
    });

    function handleFileSelect(e) {
        const file = e.target.files[0];
        if (file) {
            // 重置JSON导入相关状态
            resetJsonImportState();
            handleFile(file);
        }
    }

    function handleFile(file) {
        selectedFile = file;
        
        // Display file info
        document.getElementById('fileName').textContent = file.name;
        document.getElementById('fileSize').textContent = formatFileSize(file.size);
        document.getElementById('fileType').textContent = file.type || 'Unknown';
        
        fileInfo.style.display = 'block';
        recognizeBtn.style.display = 'inline-block';
        recognizeBtn.disabled = false;
        
        hideMessages();
    }

    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    async function recognizeAudio() {
        if (!selectedFile) {
            alert('音频文件未加载，请先选择音频文件');
            return;
        }

        // Show progress
        progressContainer.style.display = 'block';
        recognizeBtn.disabled = true;
        recognizeBtn.innerHTML = '<span class="loading"></span>转换并识别中...';
        hideMessages();
        resultsSection.style.display = 'none';

        // Simulate progress
        let progress = 0;
        const progressInterval = setInterval(() => {
            progress += Math.random() * 10;
            if (progress > 85) progress = 85;
            progressFill.style.width = progress + '%';
        }, 200);

        try {
            let audioFileToRecognize = selectedFile;
            
            // Step 1: Convert audio to MP3 if not already MP3
            const fileExtension = selectedFile.name.split('.').pop().toLowerCase();
            if (fileExtension !== 'mp3') {
                console.log(`Converting ${selectedFile.name} from ${fileExtension} to MP3...`);
                
                const convertFormData = new FormData();
                convertFormData.append('audio', selectedFile);
                
                const convertResponse = await fetch('/api/convert_to_mp3', {
                    method: 'POST',
                    body: convertFormData
                });
                
                if (!convertResponse.ok) {
                    throw new Error('音频转换失败');
                }
                
                // Get the converted MP3 file as blob
                const mp3Blob = await convertResponse.blob();
                const originalName = selectedFile.name.split('.').slice(0, -1).join('.');
                audioFileToRecognize = new File([mp3Blob], `${originalName}.mp3`, { type: 'audio/mpeg' });
                
                console.log('Audio converted to MP3 successfully');
                showSuccess('音频已转换为MP3格式，开始识别...');
                
                // Update progress
                progress = 30;
                progressFill.style.width = progress + '%';
            } else {
                console.log('Audio is already in MP3 format, proceeding with recognition...');
            }
            
            // Step 2: Perform recognition with the MP3 file
            const recognizeFormData = new FormData();
            recognizeFormData.append('audio', audioFileToRecognize);
            
            const response = await fetch('/api/recognize', {
                method: 'POST',
                body: recognizeFormData
            });

            const result = await response.json();

            clearInterval(progressInterval);
            progressFill.style.width = '100%';

            setTimeout(() => {
                progressContainer.style.display = 'none';
                progressFill.style.width = '0%';
                recognizeBtn.disabled = false;
                recognizeBtn.innerHTML = '重新识别';

                if (result.success) {
                    displayResults(result);
                    
                    // 识别完成后自动保存音频文件到results文件夹（保存转换后的MP3文件）
                    if (audioFileToRecognize && result.result_id) {
                        console.log('识别完成，开始保存MP3音频文件到results文件夹...');
                        uploadAudioForResult(audioFileToRecognize, result.result_id);
                    }
                    
                    const conversionMsg = fileExtension !== 'mp3' ? '（已转换为MP3格式）' : '';
                    showSuccess(`识别完成！${conversionMsg}`);
                } else {
                    showError(result.message || '识别失败');
                }
            }, 500);

        } catch (error) {
            clearInterval(progressInterval);
            progressContainer.style.display = 'none';
            progressFill.style.width = '0%';
            recognizeBtn.disabled = false;
            recognizeBtn.innerHTML = '开始识别';
            showError('处理错误: ' + error.message);
        }
    }

    let currentResult = null; // 存储当前识别结果
    let audioPlayer = null; // 音频播放器引用
    let currentAudioFile = null; // 当前音频文件
    let isEditMode = false; // 编辑模式状态
    let isBilingualMode = true; // 双语模式状态，默认开启
    let selectedSentences = new Set(); // 选中的分句索引

    function displayResults(result) {
        currentResult = result; // 保存当前结果
        
        // Update statistics
        document.getElementById('totalDuration').textContent = result.total_duration || 0;
        document.getElementById('sentenceCount').textContent = result.sentences.length;
        document.getElementById('speakerCount').textContent = result.speakers.length;
        document.getElementById('wordCount').textContent = result.text.length;

        // Display full text
        document.getElementById('fullText').textContent = result.text;
        // 初始化时隐藏完整文本内容
        document.getElementById('fullText').style.display = 'none';
        // 更新按钮文本
        const toggleBtn = document.getElementById('toggleFullTextBtn');
        if (toggleBtn) {
            toggleBtn.innerHTML = '🔽 显示完整文本';
        }

        // 设置音频播放器
        setupAudioPlayer();

        // Display sentences
        const sentencesList = document.getElementById('sentencesList');
        sentencesList.innerHTML = '';

        result.sentences.forEach((sentence, index) => {
            const sentenceDiv = document.createElement('div');
            sentenceDiv.className = 'sentence-item';
            sentenceDiv.dataset.start = sentence.start;
            sentenceDiv.dataset.end = sentence.end;
            sentenceDiv.dataset.index = index;
            
            const speakerColors = ['#4facfe', '#00f2fe', '#667eea', '#764ba2', '#f093fb', '#f5576c'];
            const speakerColor = speakerColors[index % speakerColors.length];
            
            // 构建翻译显示内容
            let translationHtml = '';
            if (sentence.translation) {
                const sourceFlag = sentence.translation.source_lang === 'zh' ? '🇨🇳' : '🇺🇸';
                const targetFlag = sentence.translation.source_lang === 'zh' ? '🇺🇸' : '🇨🇳';
                
                const displayStyle = isBilingualMode ? 'block' : 'none';
                translationHtml = `
                    <div id="sentence-translation-${index}" style="margin-top: 3px; color: #555555; font-style: italic; font-size: 14px; display: ${displayStyle};">${sentence.translation.source_lang === 'zh' ? sentence.translation.en : sentence.translation.zh}</div>
                `;
            }
            
            sentenceDiv.innerHTML = `
                <div class="sentence-header">
                    <span class="speaker-tag" style="background: ${speakerColor}">${sentence.speaker}</span>
                    <span class="timestamp">🎵 ${formatTimeToHMS(sentence.start)} - ${formatTimeToHMS(sentence.end)}</span>
                    <div class="sentence-buttons">
                        <button class="edit-text-btn" onclick="toggleTextEdit(${index}, event)">✏️ 编辑</button>
                        <button class="merge-prev-btn" onclick="mergeWithPrevious(${index}, event)">&uarr; 合并</button>
                    </div>
                </div>
                <div class="sentence-text" id="sentence-text-${index}">${sentence.text}</div>
                <textarea class="sentence-edit-input" id="sentence-edit-${index}" style="display: none; width: 100%; min-height: 60px; padding: 8px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px; resize: vertical;">${sentence.text}</textarea>
                ${translationHtml}
            `;
            
            // 添加点击事件监听器
            sentenceDiv.addEventListener('click', (e) => {
                if (isEditMode) {
                    e.preventDefault();
                    toggleSentenceSelection(index, sentenceDiv);
                } else {
                    // 检查当前分句是否正在播放
                    if (sentenceDiv.classList.contains('playing')) {
                        // 如果正在播放，则暂停
                        if (audioPlayer) {
                            audioPlayer.pause();
                            sentenceDiv.classList.remove('playing');
                        }
                    } else {
                        // 如果没有播放，则播放当前分句
                        playAudioSegment(parseFloat(sentenceDiv.dataset.start), parseFloat(sentenceDiv.dataset.end), sentenceDiv);
                    }
                }
            });
            
            sentencesList.appendChild(sentenceDiv);
        });

        // 显示操作按钮
        document.getElementById('resultActions').style.display = 'block';
        
        resultsSection.style.display = 'block';
    }

    function showError(message) {
        errorMessage.textContent = message;
        errorMessage.style.display = 'block';
        successMessage.style.display = 'none';
    }

    function showSuccess(message) {
        successMessage.textContent = message;
        successMessage.style.display = 'block';
        errorMessage.style.display = 'none';
    }

    function hideMessages() {
        errorMessage.style.display = 'none';
        successMessage.style.display = 'none';
    }

    // 重置JSON导入相关状态
    function resetJsonImportState() {
        importedJsonData = null;
        selectedAudioForJson = null;
        selectAudioBtn.style.display = 'none';
        selectAudioBtn.textContent = '🎵 选择对应音频';
        selectAudioBtn.style.background = 'linear-gradient(135deg, #fd79a8 0%, #fdcb6e 100%)';
        audioForJsonInput.value = '';
    }

    // 处理JSON文件导入
    function handleJsonImport(e) {
        const file = e.target.files[0];
        if (!file) return;

        // 重置之前的状态
        resetJsonImportState();

        if (!file.name.toLowerCase().endsWith('.json')) {
            showError('请选择JSON格式的文件');
            return;
        }

        const reader = new FileReader();
        reader.onload = function(event) {
            try {
                console.log('开始解析JSON文件:', file.name);
                const jsonData = JSON.parse(event.target.result);
                console.log('JSON解析成功，数据结构:', jsonData);
                
                // 验证JSON格式是否正确
                if (!validateJsonFormat(jsonData)) {
                    showError('JSON文件格式不正确。请检查浏览器控制台查看详细错误信息。确保文件包含必要字段：text、sentences、speakers');
                    return;
                }

                // 确保数据包含必要的统计信息
                if (!jsonData.total_duration) {
                    jsonData.total_duration = jsonData.sentences.length > 0 ? 
                        Math.max(...jsonData.sentences.map(s => s.end)) : 0;
                }

                // 保存导入的JSON数据
                importedJsonData = jsonData;
                
                // 显示导入的结果
                displayResults(jsonData);
                
                // 显示选择音频按钮（如果JSON包含audio_hash）
                if (jsonData.audio_hash) {
                    selectAudioBtn.style.display = 'inline-block';
                    const audioFileName = jsonData.filename ? `（原音频文件：${jsonData.filename}）` : '';
                    showSuccess(`成功导入识别结果：${file.name}。如需播放音频，请选择对应的音频文件进行验证${audioFileName}。`);
                } else {
                    const audioFileName = jsonData.filename ? `（原音频文件：${jsonData.filename}）` : '';
                    showSuccess(`成功导入识别结果：${file.name}${audioFileName}`);
                }
                
                // 隐藏文件信息和识别按钮
                fileInfo.style.display = 'none';
                recognizeBtn.style.display = 'none';
                
            } catch (error) {
                console.error('JSON解析错误:', error);
                showError('JSON文件解析失败：' + error.message + '。请确保文件是有效的JSON格式。');
            }
        };
        
        reader.onerror = function() {
            showError('文件读取失败');
        };
        
        reader.readAsText(file);
    }

    // 验证JSON格式
    function validateJsonFormat(data) {
        // 检查必要的字段
        const requiredFields = ['text', 'sentences', 'speakers'];
        for (const field of requiredFields) {
            if (!(field in data)) {
                console.log(`Missing required field: ${field}`);
                return false;
            }
        }

        // 检查sentences数组格式
        if (!Array.isArray(data.sentences)) {
            console.log('sentences is not an array');
            return false;
        }

        // 检查每个句子的格式（更宽松的验证）
        for (let i = 0; i < data.sentences.length; i++) {
            const sentence = data.sentences[i];
            if (!sentence.hasOwnProperty('text')) {
                console.log(`Sentence ${i} missing text field`);
                return false;
            }
            if (!sentence.hasOwnProperty('start') || typeof sentence.start !== 'number') {
                console.log(`Sentence ${i} missing or invalid start field`);
                return false;
            }
            if (!sentence.hasOwnProperty('end') || typeof sentence.end !== 'number') {
                console.log(`Sentence ${i} missing or invalid end field`);
                return false;
            }
            if (!sentence.hasOwnProperty('speaker')) {
                console.log(`Sentence ${i} missing speaker field`);
                return false;
            }
        }

        // 检查speakers数组
        if (!Array.isArray(data.speakers)) {
            console.log('speakers is not an array');
            return false;
        }

        console.log('JSON validation passed');
        return true;
    }

    // 处理音频文件选择（用于JSON导入后的音频验证）
    function handleAudioForJsonSelect(e) {
        const file = e.target.files[0];
        if (!file) return;

        if (!importedJsonData) {
            alert('音频文件未加载：请先导入JSON结果文件');
            return;
        }

        // 检查文件类型
        const allowedTypes = ['audio/wav', 'audio/mpeg', 'audio/mp4', 'audio/flac', 'audio/aac', 'audio/ogg'];
        if (!allowedTypes.includes(file.type) && !file.name.match(/\.(wav|mp3|m4a|flac|aac|ogg)$/i)) {
            alert('音频文件未加载：不支持的音频格式，请选择wav、mp3、m4a、flac、aac或ogg格式的文件');
            return;
        }

        // 显示处理状态
            showSuccess('正在计算音频文件hash值，请稍候...');
            
            // 计算音频文件的MD5 hash
            const reader = new FileReader();
            reader.onload = function(event) {
                try {
                    const arrayBuffer = event.target.result;
                    const calculatedHash = calculateMD5Hash(arrayBuffer);
                    
                    console.log('计算的音频hash:', calculatedHash);
                    console.log('JSON中的hash:', importedJsonData.audio_hash);
                    
                    if (calculatedHash === importedJsonData.audio_hash) {
                        // Hash匹配，设置音频文件
                        selectedAudioForJson = file;
                        selectedFile = file; // 设置为当前音频文件
                        setupAudioPlayer(file);
                        
                        // 上传音频文件到服务器并更新JSON
                        uploadAudioForResult(file, importedJsonData.result_id);
                        
                        showSuccess(`音频文件验证成功！Hash值匹配，现在可以播放音频片段。`);
                        selectAudioBtn.textContent = '✅ 音频已验证';
                        selectAudioBtn.style.background = 'linear-gradient(135deg, #00b894 0%, #00cec9 100%)';
                    } else {
                        alert(`音频文件未加载：Hash值不匹配，请选择正确的音频文件\n期望: ${importedJsonData.audio_hash}\n实际: ${calculatedHash}`);
                    }
                } catch (error) {
                    console.error('Hash计算错误:', error);
                    alert('音频文件未加载：hash计算失败 - ' + error.message);
                }
            };
        
        reader.onerror = function() {
            alert('音频文件未加载：文件读取失败，请重新选择音频文件');
        };
        
        reader.readAsArrayBuffer(file);
    }

    // 使用crypto-js计算MD5 hash
        function calculateMD5Hash(arrayBuffer) {
            // 将ArrayBuffer转换为WordArray
            const wordArray = CryptoJS.lib.WordArray.create(arrayBuffer);
            // 计算MD5 hash
            const hash = CryptoJS.MD5(wordArray).toString();
            return hash;
        }

    // 上传音频文件到服务器并更新JSON
        async function uploadAudioForResult(audioFile, resultId) {
            console.log('开始上传音频文件:', audioFile.name, 'resultId:', resultId);
            try {
                const formData = new FormData();
                formData.append('audio', audioFile);
                
                console.log('发送上传请求到:', `/api/upload_audio/${resultId}`);
                const response = await fetch(`/api/upload_audio/${resultId}`, {
                    method: 'POST',
                    body: formData
                });
                
                console.log('上传响应状态:', response.status);
                const result = await response.json();
                console.log('上传响应结果:', result);
                
                if (result.success) {
                    // 更新JSON数据中的音频路径
                    if (importedJsonData) {
                        importedJsonData.audio_path = result.audio_path;
                        console.log('已更新 importedJsonData.audio_path:', result.audio_path);
                    }
                    // 同时更新currentResult中的音频路径
                    if (currentResult) {
                        currentResult.audio_path = result.audio_path;
                        console.log('已更新 currentResult.audio_path:', result.audio_path);
                    }
                    // 自动同步更新到服务器
                    console.log('开始自动同步结果到服务器...');
                    await autoSyncResult();
                    console.log('音频文件已上传并保存路径到JSON:', result.audio_path);
                } else {
                    console.error('音频文件上传失败:', result.message);
                }
            } catch (error) {
                console.error('音频文件上传错误:', error);
            }
        }

        // 从服务器加载保存的音频文件
        async function loadSavedAudioFile(audioPath) {
            try {
                const response = await fetch(`/api/audio/${audioPath}`);
                if (response.ok) {
                    const audioBlob = await response.blob();
                    const audioFile = new File([audioBlob], audioPath, { type: audioBlob.type });
                    
                    // 设置为当前音频文件
                    selectedFile = audioFile;
                    selectedAudioForJson = audioFile;
                    
                    // 设置音频播放器
                    setupAudioPlayer(audioFile);
                    
                    console.log('保存的音频文件已加载:', audioPath);
                } else {
                    console.error('加载保存的音频文件失败:', response.statusText);
                    // 如果音频文件不存在，显示选择音频按钮
                    if (importedJsonData && importedJsonData.audio_hash) {
                        selectAudioBtn.style.display = 'inline-block';
                        selectAudioBtn.textContent = '🎵 选择对应音频';
                        selectAudioBtn.style.background = 'linear-gradient(135deg, #fd79a8 0%, #fdcb6e 100%)';
                    }
                }
            } catch (error) {
                console.error('加载保存的音频文件错误:', error);
                // 如果加载失败，显示选择音频按钮
                if (importedJsonData && importedJsonData.audio_hash) {
                    selectAudioBtn.style.display = 'inline-block';
                    selectAudioBtn.textContent = '🎵 选择对应音频';
                    selectAudioBtn.style.background = 'linear-gradient(135deg, #fd79a8 0%, #fdcb6e 100%)';
                }
            }
        }

    // 设置音频播放器
    function setupAudioPlayer(audioFile = null) {
        audioPlayer = document.getElementById('audioPlayer');
        const fileToUse = audioFile || selectedFile;
        
        if (fileToUse && currentAudioFile !== fileToUse) {
            currentAudioFile = fileToUse;
            const audioURL = URL.createObjectURL(fileToUse);
            audioPlayer.src = audioURL;
            audioPlayer.style.display = 'block';
            
            // 清理之前的URL对象
            audioPlayer.addEventListener('loadstart', () => {
                if (audioPlayer.src && audioPlayer.src.startsWith('blob:')) {
                    // 不立即清理，等播放完成后再清理
                }
            });
        }
        
        // 添加播放进度监听器，实现播放器与分句列表的双向绑定
        if (audioPlayer && !audioPlayer.hasAttribute('data-progress-listener')) {
            audioPlayer.setAttribute('data-progress-listener', 'true');
            
            // 监听播放进度变化
            audioPlayer.addEventListener('timeupdate', function() {
                highlightCurrentSentence(this.currentTime);
            });
            
            // 监听播放结束事件
            audioPlayer.addEventListener('ended', function() {
                // 移除所有高亮
                document.querySelectorAll('.sentence-item.playing').forEach(item => {
                    item.classList.remove('playing');
                });
            });
        }
    }
    
    // 高亮显示当前播放时间对应的分句
    function highlightCurrentSentence(currentTime) {
        // 移除之前的所有高亮
        document.querySelectorAll('.sentence-item.playing').forEach(item => {
            item.classList.remove('playing');
        });
        
        // 查找当前时间对应的分句
        const sentences = document.querySelectorAll('.sentence-item');
        let currentSentence = null;
        
        for (let i = 0; i < sentences.length; i++) {
            const start = parseFloat(sentences[i].dataset.start);
            const end = parseFloat(sentences[i].dataset.end);
            
            if (currentTime >= start && currentTime <= end) {
                currentSentence = sentences[i];
                break;
            }
        }
        
        // 如果找到了对应的分句
        if (currentSentence) {
            currentSentence.classList.add('playing');
            
            // 自动滚动到对应的分句
            const container = document.querySelector('.sentences-list-wrapper');
            if (container) {
                const containerRect = container.getBoundingClientRect();
                const sentenceRect = currentSentence.getBoundingClientRect();
                
                // 检查元素是否在可视区域内
                if (sentenceRect.top < containerRect.top || sentenceRect.bottom > containerRect.bottom) {
                    // 计算滚动位置，使元素居中
                    const scrollTop = currentSentence.offsetTop - container.offsetTop - container.clientHeight / 2 + currentSentence.clientHeight / 2;
                    container.scrollTo({
                        top: scrollTop,
                        behavior: 'smooth'
                    });
                }
            }
        }
    }

    // 播放音频片段
    function playAudioSegment(startTime, endTime, sentenceElement) {
        if (!audioPlayer || !audioPlayer.src) {
            alert('音频文件未加载，请先选择并加载音频文件');
            return;
        }

        // 移除之前的播放状态
        document.querySelectorAll('.sentence-item.playing').forEach(item => {
            item.classList.remove('playing');
        });

        // 添加当前播放状态
        sentenceElement.classList.add('playing');

        // 设置播放时间
        audioPlayer.currentTime = startTime;
        
        // 播放音频
        audioPlayer.play().catch(error => {
            console.error('播放失败:', error);
            alert('音频文件未加载或播放失败，请检查文件格式或重新选择音频文件');
            sentenceElement.classList.remove('playing');
        });

        // 监听时间更新，在指定时间停止
        const timeUpdateHandler = () => {
            if (audioPlayer.currentTime >= endTime) {
                audioPlayer.pause();
                sentenceElement.classList.remove('playing');
                audioPlayer.removeEventListener('timeupdate', timeUpdateHandler);
            }
        };

        audioPlayer.addEventListener('timeupdate', timeUpdateHandler);

        // 如果用户手动暂停，也要移除播放状态
        const pauseHandler = () => {
            sentenceElement.classList.remove('playing');
            audioPlayer.removeEventListener('timeupdate', timeUpdateHandler);
            audioPlayer.removeEventListener('pause', pauseHandler);
        };

        audioPlayer.addEventListener('pause', pauseHandler);
    }

    // 自动同步更新结果到JSON文件
    async function autoSyncResult() {
        if (!currentResult || !currentResult.result_id) {
            // 如果没有result_id，说明还没有保存过，先保存
            await saveResult();
            return;
        }

        try {
            const response = await fetch(`/api/update_result/${currentResult.result_id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(currentResult)
            });

            const result = await response.json();
            if (result.success) {
                console.log('结果已自动同步更新');
                return Promise.resolve();
            } else {
                console.error('自动同步失败:', result.message);
                return Promise.reject(new Error(result.message));
            }
        } catch (error) {
            console.error('自动同步失败:', error.message);
            return Promise.reject(error);
        }
    }

    // 保存识别结果
    async function saveResult() {
        if (!currentResult) {
            showError('没有可保存的结果');
            return Promise.reject(new Error('没有可保存的结果'));
        }

        try {
            const response = await fetch('/api/save_result', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(currentResult)
            });

            const result = await response.json();
            if (result.success) {
                // 保存成功后更新currentResult的result_id
                currentResult.result_id = result.result_id;
                showSuccess(`结果已保存！ID: ${result.result_id}`);
                return Promise.resolve();
            } else {
                showError('保存失败: ' + result.message);
                return Promise.reject(new Error(result.message));
            }
        } catch (error) {
            showError('保存失败: ' + error.message);
            return Promise.reject(error);
        }
    }

    // 导出识别结果
    async function exportResult() {
        if (!currentResult || !currentResult.result_id) {
            showError('请先保存结果再导出');
            return;
        }

        try {
            const link = document.createElement('a');
            link.href = `/api/export/${currentResult.result_id}`;
            link.download = `astromao_result_${currentResult.result_id}.json`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            showSuccess('结果已导出！');
        } catch (error) {
            showError('导出失败: ' + error.message);
        }
    }

    // 显示历史记录
    async function showResultsHistory() {
        try {
            const response = await fetch('/api/results');
            const data = await response.json();
            
            if (data.success) {
                displayHistoryList(data.results);
                document.getElementById('historyModal').style.display = 'block';
            } else {
                showError('获取历史记录失败');
            }
        } catch (error) {
            showError('获取历史记录失败: ' + error.message);
        }
    }

    // 显示历史记录列表
    function displayHistoryList(results) {
        const historyList = document.getElementById('historyList');
        
        if (results.length === 0) {
            historyList.innerHTML = '<p style="text-align: center; color: #666;">暂无历史记录</p>';
            return;
        }

        historyList.innerHTML = results.map(result => `
            <div style="border: 1px solid #ddd; border-radius: 8px; padding: 15px; margin-bottom: 10px; background: #f9f9f9;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <div>
                        <strong>${result.filename}</strong>
                        ${result.original_filename ? `<div style="color: #666; font-size: 0.85em; margin-top: 2px;">原音频: ${result.original_filename}</div>` : ''}
                    </div>
                    <span style="color: #666; font-size: 0.9em;">${new Date(result.timestamp).toLocaleString()}</span>
                </div>
                <div style="margin-bottom: 10px;">
                    <div style="color: #666; font-size: 0.9em;">音频Hash: ${result.audio_hash}</div>
                    <div style="color: #666; font-size: 0.9em;">时长: ${result.total_duration}秒 | 说话人: ${result.speakers_count} | 句子: ${result.sentences_count}</div>
                </div>
                <div style="margin-bottom: 10px; color: #333;">${result.text_preview}</div>
                <div style="text-align: right;">
                    <button onclick="loadHistoryResult('${result.result_id}')" class="history-action-btn load-btn">📂 加载</button>
                    <button onclick="exportHistoryResult('${result.result_id}')" class="history-action-btn export-btn">📥 导出</button>
                    <button onclick="deleteHistoryResult('${result.result_id}')" class="history-action-btn delete-btn">🗑️ 删除</button>
                </div>
            </div>
        `).join('');
    }

    // 加载历史记录结果
    async function loadHistoryResult(resultId) {
        try {
            const response = await fetch(`/api/export/${resultId}`);
            if (!response.ok) {
                throw new Error('获取历史记录失败');
            }
            
            const jsonData = await response.json();
            
            // 关闭历史记录模态框
            closeHistoryModal();
            
            // 重置状态
            resetJsonImportState();
            selectedFile = null;
            
            // 设置导入的JSON数据
            importedJsonData = jsonData;
            
            // 重要：为历史记录数据设置result_id，以便后续编辑时能正确更新
            jsonData.result_id = resultId;
            
            // 显示结果
            displayResults(jsonData);
            
            // 检查是否有保存的音频路径
            if (jsonData.audio_path) {
                // 自动加载保存的音频文件
                loadSavedAudioFile(jsonData.audio_path);
                const audioFileName = jsonData.filename ? `（原音频文件：${jsonData.filename}）` : '';
                showSuccess(`历史记录已加载！音频文件已自动加载${audioFileName}`);
            } else if (jsonData.audio_hash) {
                // 如果有音频哈希但没有保存的音频路径，显示选择音频按钮
                selectAudioBtn.style.display = 'inline-block';
                selectAudioBtn.textContent = '🎵 选择对应音频';
                selectAudioBtn.style.background = 'linear-gradient(135deg, #fd79a8 0%, #fdcb6e 100%)';
                const audioFileName = jsonData.filename ? `（原音频文件：${jsonData.filename}）` : '';
                showSuccess(`历史记录已加载！请选择对应的音频文件进行验证${audioFileName}（音频哈希: ${jsonData.audio_hash.substring(0, 8)}...）`);
            } else {
                const audioFileName = jsonData.filename ? `（原音频文件：${jsonData.filename}）` : '';
                showSuccess(`历史记录已加载！${audioFileName}`);
            }
            
            // 隐藏文件信息和识别按钮
            fileInfo.style.display = 'none';
            recognizeBtn.style.display = 'none';
            
        } catch (error) {
            showError('加载历史记录失败: ' + error.message);
        }
    }

    // 导出历史记录结果
    async function exportHistoryResult(resultId) {
        try {
            const link = document.createElement('a');
            link.href = `/api/export/${resultId}`;
            link.download = `astromao_result_${resultId}.json`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            showSuccess('结果已导出！');
        } catch (error) {
            showError('导出失败: ' + error.message);
        }
    }

    // 删除历史记录结果
    async function deleteHistoryResult(resultId) {
        if (!confirm('确定要删除这个结果吗？')) {
            return;
        }

        try {
            const response = await fetch(`/api/results/${resultId}`, {
                method: 'DELETE'
            });

            const result = await response.json();
            if (result.success) {
                showSuccess('结果已删除！');
                showResultsHistory(); // 刷新历史记录列表
            } else {
                showError('删除失败: ' + result.message);
            }
        } catch (error) {
            showError('删除失败: ' + error.message);
        }
    }

    // 关闭历史记录模态框
    function closeHistoryModal() {
        document.getElementById('historyModal').style.display = 'none';
    }

    // 切换完整文本显示状态
    function toggleFullText() {
        const fullTextDiv = document.getElementById('fullText');
        const toggleBtn = document.getElementById('toggleFullTextBtn');
        
        if (fullTextDiv && toggleBtn) {
            // 检查完整文本当前是否可见
            if (fullTextDiv.style.display === 'none') {
                // 当前隐藏，需要显示
                fullTextDiv.style.display = 'block';
                toggleBtn.innerHTML = '🔼 隐藏完整文本';
            } else {
                // 当前显示，需要隐藏
                fullTextDiv.style.display = 'none';
                toggleBtn.innerHTML = '🔽 显示完整文本';
            }
        }
    }

    // 切换文本编辑状态
    function toggleTextEdit(index, event) {
        event.stopPropagation(); // 阻止事件冒泡
        
        const textElement = document.getElementById(`sentence-text-${index}`);
        const inputElement = document.getElementById(`sentence-edit-${index}`);
        const editBtn = event.target;
        
        if (textElement.style.display !== 'none') {
            // 进入编辑状态
            textElement.style.display = 'none';
            inputElement.style.display = 'block';
            inputElement.focus();
            editBtn.textContent = '💾 保存';
            editBtn.style.background = '#007bff';
        } else {
            // 保存编辑结果
            const newText = inputElement.value.trim();
            if (newText === '') {
                showError('文本内容不能为空');
                return;
            }
            
            // 更新当前结果中的文本
            if (currentResult && currentResult.sentences[index]) {
                const oldText = currentResult.sentences[index].text;
                currentResult.sentences[index].text = newText;
                textElement.textContent = newText;
                
                // 重新生成完整文本
                currentResult.text = currentResult.sentences.map(s => s.text).join(' ');
                document.getElementById('fullText').textContent = currentResult.text;
                
                // 更新字符数统计
                document.getElementById('wordCount').textContent = currentResult.text.length;
                
                // 显示正在翻译的提示
                showSuccess('正在重新翻译文本...');
                
                // 调用翻译API重新翻译当前句子
                translateText(newText)
                    .then(translation => {
                        // 更新翻译结果
                        currentResult.sentences[index].translation = translation;
                        
                        // 更新UI显示翻译结果
                        // 首先查找现有的翻译元素
                        let translationElement = document.getElementById(`sentence-translation-${index}`);
                        
                        // 如果没找到特定ID的翻译元素，尝试查找在句子文本后面的div元素
                        if (!translationElement) {
                            const sentenceTextElement = document.getElementById(`sentence-text-${index}`);
                            // 查找紧随句子文本后的div元素（可能是之前渲染的翻译元素）
                            let nextElement = sentenceTextElement.nextSibling;
                            while (nextElement && nextElement.nodeType !== 1) { // 跳过文本节点和其他非元素节点
                                nextElement = nextElement.nextSibling;
                            }
                            
                            // 检查下一个元素是否是翻译元素（通过样式判断）
                            if (nextElement && 
                                nextElement.tagName === 'DIV' && 
                                nextElement.style.color === 'rgb(85, 85, 85)' && 
                                nextElement.style.fontStyle === 'italic' &&
                                nextElement.style.fontSize === '14px') {
                                translationElement = nextElement;
                                translationElement.id = `sentence-translation-${index}`; // 给它分配ID方便下次查找
                            }
                        }
                        
                        // 如果仍然没有找到翻译元素，则创建一个新的
                        if (!translationElement) {
                            translationElement = document.createElement('div');
                            translationElement.id = `sentence-translation-${index}`;
                            translationElement.style.marginTop = '3px';
                            translationElement.style.color = '#555555';
                            translationElement.style.fontStyle = 'italic';
                            translationElement.style.fontSize = '14px';
                            
                            // 插入到句子文本后面
                            const sentenceTextElement = document.getElementById(`sentence-text-${index}`);
                            sentenceTextElement.parentNode.insertBefore(translationElement, sentenceTextElement.nextSibling);
                        }
                        
                        // 更新翻译内容
                        if (translation) {
                            const translationText = typeof translation === 'object' ? 
                                (translation.zh || translation.en || JSON.stringify(translation)) : 
                                translation;
                            translationElement.textContent = translationText;
                            translationElement.style.display = 'block';
                        } else {
                            translationElement.style.display = 'none';
                        }
                        
                        // 自动同步更新JSON文件
                        return autoSyncResult();
                    })
                    .then(() => {
                        showSuccess('文本已保存并完成翻译！');
                    })
                    .catch(error => {
                        // 回滚文本更改
                        currentResult.sentences[index].text = oldText;
                        textElement.textContent = oldText;
                        
                        // 重新生成完整文本
                        currentResult.text = currentResult.sentences.map(s => s.text).join(' ');
                        document.getElementById('fullText').textContent = currentResult.text;
                        
                        // 更新字符数统计
                        document.getElementById('wordCount').textContent = currentResult.text.length;
                        
                        showError('保存失败: ' + error.message);
                    });
            }
            
            // 退出编辑状态
            textElement.style.display = 'block';
            inputElement.style.display = 'none';
            editBtn.textContent = '✏️ 编辑';
            editBtn.style.background = '#28a745';
        }
    }

    // 调用翻译API
    async function translateText(text) {
        console.log('translateText函数被调用，输入文本:', text);
        try {
            console.log('发送翻译请求到 /api/translate');
            const response = await fetch('/api/translate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    text: text,
                    target_lang: 'auto'
                })
            });
            console.log('收到响应，状态:', response.status);
            
            const result = await response.json();
            console.log('解析后的响应结果:', result);
            
            if (result.success) {
                console.log('翻译成功，返回翻译结果:', result.translation);
                return result.translation;
            } else {
                console.error('翻译失败，错误信息:', result.error);
                throw new Error(result.error || '翻译失败');
            }
        } catch (error) {
            console.error('翻译API调用失败，错误详情:', error);
            console.error('错误类型:', error.name);
            console.error('错误消息:', error.message);
            if (error.stack) {
                console.error('错误堆栈:', error.stack);
            }
            throw error;
        }
    }

    // 合并选中的分句并重新翻译
    async function mergeAndTranslateSentences() {
        console.log('mergeAndTranslateSentences 函数被调用');
        if (selectedSentences.size < 2) {
            showError('请至少选择2个分句进行合并');
            return;
        }
        
        // 将选中的索引转换为数组并排序
        const selectedIndices = Array.from(selectedSentences).sort((a, b) => a - b);
        
        // 检查选中的分句是否连续
        let isConsecutive = true;
        for (let i = 1; i < selectedIndices.length; i++) {
            if (selectedIndices[i] !== selectedIndices[i-1] + 1) {
                isConsecutive = false;
                break;
            }
        }
        
        if (!isConsecutive) {
            if (!confirm('选中的分句不连续，合并后可能影响时间轴的连贯性。是否继续？')) {
                return;
            }
        }
        
        // 获取要合并的分句
        const sentencesToMerge = selectedIndices.map(index => currentResult.sentences[index]);
        
        // 检查说话人是否一致
        const speakers = [...new Set(sentencesToMerge.map(s => s.speaker))];
        if (speakers.length > 1) {
            const speakerList = speakers.join(', ');
            if (!confirm(`选中的分句包含不同的说话人（${speakerList}），合并后将使用第一个说话人（${speakers[0]}）。是否继续？`)) {
                return;
            }
        }
        
        // 合并文本
        const mergedText = sentencesToMerge.map(s => s.text).join(' ');
        
        try {
            // 显示翻译进度
            showSuccess('正在重新翻译合并后的文本...');
            
            // 调用翻译API
            console.log('开始调用翻译API，文本:', mergedText);
            const translation = await translateText(mergedText);
            console.log('翻译API返回结果:', translation);
            
            // 创建合并后的分句（包含新的翻译）
            const mergedSentence = {
                start: sentencesToMerge[0].start,
                end: sentencesToMerge[sentencesToMerge.length - 1].end,
                text: mergedText,
                speaker: sentencesToMerge[0].speaker,
                translation: translation
            };
            
            // 创建新的分句数组
            const newSentences = [];
            let mergedAdded = false;
            
            for (let i = 0; i < currentResult.sentences.length; i++) {
                if (selectedIndices.includes(i)) {
                    // 如果是第一个选中的分句，添加合并后的分句
                    if (i === selectedIndices[0] && !mergedAdded) {
                        newSentences.push(mergedSentence);
                        mergedAdded = true;
                    }
                    // 跳过其他选中的分句
                } else {
                    newSentences.push(currentResult.sentences[i]);
                }
            }
            
            // 更新结果
            currentResult.sentences = newSentences;
            currentResult.text = newSentences.map(s => s.text).join(' ');
            
            // 重新显示结果
            displayResults(currentResult);
            
            // 退出编辑模式
            toggleEditMode();
            
            // 自动同步更新JSON文件
            autoSyncResult();
            
            // 清除选择状态
            clearSelection();
            
            showSuccess(`成功合并了 ${selectedIndices.length} 个分句并重新翻译！`);
            
        } catch (error) {
            showError('翻译失败: ' + error.message);
        }
    }

    // 合并选中的分句
    function mergeSelectedSentences() {
        if (selectedSentences.size < 2) {
            showError('请至少选择2个分句进行合并');
            return;
        }
        
        if (!currentResult || !currentResult.sentences) {
            showError('没有可用的识别结果');
            return;
        }
        
        // 将选中的索引转换为数组并排序
        const selectedIndices = Array.from(selectedSentences).sort((a, b) => a - b);
        
        // 检查选中的分句是否连续
        let isConsecutive = true;
        for (let i = 1; i < selectedIndices.length; i++) {
            if (selectedIndices[i] !== selectedIndices[i-1] + 1) {
                isConsecutive = false;
                break;
            }
        }
        
        if (!isConsecutive) {
            if (!confirm('选中的分句不连续，合并后可能影响时间轴的连贯性。是否继续？')) {
                return;
            }
        }
        
        // 获取要合并的分句
        const sentencesToMerge = selectedIndices.map(index => currentResult.sentences[index]);
        
        // 创建合并后的分句
        const mergedSentence = {
            start: Math.min(...sentencesToMerge.map(s => s.start)),
            end: Math.max(...sentencesToMerge.map(s => s.end)),
            text: sentencesToMerge.map(s => s.text).join(' '),
            speaker: sentencesToMerge[0].speaker // 使用第一个分句的说话人
        };
        
        // 检查是否有不同的说话人
        const speakers = [...new Set(sentencesToMerge.map(s => s.speaker))];
        if (speakers.length > 1) {
            const speakerList = speakers.join(', ');
            if (!confirm(`选中的分句包含不同的说话人（${speakerList}），合并后将使用第一个说话人（${speakers[0]}）。是否继续？`)) {
                return;
            }
        }
        
        // 创建新的分句数组
        const newSentences = [];
        let mergedAdded = false;
        
        for (let i = 0; i < currentResult.sentences.length; i++) {
            if (selectedIndices.includes(i)) {
                // 如果是第一个选中的分句，添加合并后的分句
                if (i === selectedIndices[0] && !mergedAdded) {
                    newSentences.push(mergedSentence);
                    mergedAdded = true;
                }
                // 跳过其他选中的分句
            } else {
                // 保留未选中的分句
                newSentences.push(currentResult.sentences[i]);
            }
        }
        
        // 更新当前结果
        currentResult.sentences = newSentences;
        
        // 重新生成完整文本
        currentResult.text = newSentences.map(s => s.text).join(' ');
        
        // 更新说话人列表
        currentResult.speakers = [...new Set(newSentences.map(s => s.speaker))];
        
        // 自动同步更新JSON文件
        autoSyncResult();
        
        // 重新显示结果
        displayResults(currentResult);
        
        // 退出编辑模式
        toggleEditMode();
        
        // 清除选择状态
        clearSelection();
        
        showSuccess(`成功合并了 ${selectedIndices.length} 个分句并同步更新！`);
    }

    // 合并当前句子与上一个句子
    function mergeWithPrevious(index, event) {
        event.stopPropagation(); // 阻止事件冒泡
        
        if (index <= 0) {
            showError('已经是第一句，无法与上一句合并');
            return;
        }
        
        if (!currentResult || !currentResult.sentences) {
            showError('没有可用的识别结果');
            return;
        }
        
        const prevSentence = currentResult.sentences[index - 1];
        const currentSentence = currentResult.sentences[index];
        
        // 检查说话人是否一致
        if (prevSentence.speaker !== currentSentence.speaker) {
            if (!confirm(`两句说话人不同（${prevSentence.speaker} vs ${currentSentence.speaker}），是否仍要合并？`)) {
                return;
            }
        }
        
        // 合并文本
        const mergedText = prevSentence.text + ' ' + currentSentence.text;
        
        // 显示提示信息
        showSuccess('注意：当前版本合并句子后只能重新翻译文本，无法重新进行语音识别。要实现完整的语音识别和翻译功能，需要后端提供相应API支持。');
        
        // 调用翻译API
        translateText(mergedText)
            .then(translation => {
                // 创建合并后的句子
                const mergedSentence = {
                    start: prevSentence.start,
                    end: currentSentence.end,
                    text: mergedText,
                    speaker: prevSentence.speaker,
                    translation: translation
                };
                
                // 构造新的句子列表
                const newSentences = [
                    ...currentResult.sentences.slice(0, index - 1),
                    mergedSentence,
                    ...currentResult.sentences.slice(index + 1)
                ];
                
                // 更新结果
                currentResult.sentences = newSentences;
                currentResult.text = newSentences.map(s => s.text).join(' ');
                
                // 更新说话人列表
                currentResult.speakers = [...new Set(newSentences.map(s => s.speaker))];
                
                // 自动同步更新JSON文件
                autoSyncResult();
                
                // 重新显示结果
                displayResults(currentResult);
                
                showSuccess('成功与上一句合并并完成翻译！');
            })
            .catch(error => {
                showError('翻译失败: ' + error.message);
            });
    }

    // 点击模态框外部关闭
    const historyModal = document.getElementById('historyModal');
    if (historyModal) {
        historyModal.addEventListener('click', function(e) {
            if (e.target === this) {
                closeHistoryModal();
            }
        });
    }

    // Check server health on page load
    if (window) {
        window.addEventListener('load', async () => {
            try {
                const response = await fetch('/api/health');
                const health = await response.json();
                if (health.status === 'healthy') {
                    console.log('Server is healthy');
                }
            } catch (error) {
                if (typeof showError !== 'undefined') {
                    showError('服务器连接失败，请检查服务是否正常运行');
                }
            }
        });
    }


// 添加一个全局的showError函数，以防在DOM加载前调用
function showError(message) {
    console.error(message);
    // 如果页面中有错误消息元素，则显示它
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            const errorElement = document.getElementById('errorMessage');
            if (errorElement) {
                errorElement.textContent = message;
                errorElement.style.display = 'block';
            }
        });
    } else {
        const errorElement = document.getElementById('errorMessage');
        if (errorElement) {
            errorElement.textContent = message;
            errorElement.style.display = 'block';
        }
    }
}
