const streamerInstances = new Map();

class VideoUploader {
    constructor() {
        this.initUploadForm();
    }

    initUploadForm() {
        const form = document.getElementById('upload-form');
        if (!form) return;

        // 视频预览功能
        document.querySelector('input[name="video"]').addEventListener('change', (e) => {
            this.previewVideo(e.target);
        });

        // 表单提交处理
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            await this.handleSubmit(e);
        });
    }

    previewVideo(input) {
        const previewContainer = document.getElementById('video-preview');
        if (!previewContainer) return;

        previewContainer.innerHTML = '';
        
        if (input.files && input.files[0]) {
            const file = input.files[0];
            
            if (!file.type.startsWith('video/')) {
                this.showError(previewContainer, '请选择有效的视频文件');
                input.value = '';
                return;
            }

            const video = document.createElement('video');
            video.controls = true;
            video.src = URL.createObjectURL(file);
            video.className = 'upload-preview';
            previewContainer.appendChild(video);
        }
    }

    async handleSubmit(e) {
        const form = e.target;
        const submitBtn = form.querySelector('button[type="submit"]');
        const originalText = submitBtn.innerHTML;

        try {
            // 显示加载状态
            submitBtn.disabled = true;
            submitBtn.innerHTML = `
                <span class="spinner-border spinner-border-sm"></span>
                提交中...
            `;

            const formData = new FormData(form);
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData,
                headers: {
                    'Accept': 'application/json'
                }
            });

            if (!response.ok) {
                const error = await response.json().catch(() => ({ error: '请求失败' }));
                throw new Error(error.error || '提交失败');
            }

            const result = await response.json();
            
            // 确保用户看到加载状态后再跳转
            setTimeout(() => {
                window.location.href = result.redirect;
            }, 500);

        } catch (error) {
            console.error('提交错误:', error);
            this.showError(form, error.message);
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalText;
        }
    }

    showError(container, message) {
        const errorAlert = document.createElement('div');
        errorAlert.className = 'alert alert-danger mt-3';
        errorAlert.innerHTML = `
            <i class="bi bi-exclamation-triangle"></i> ${message}
        `;
        container.appendChild(errorAlert);
        setTimeout(() => errorAlert.remove(), 5000);
    }
}

class VideoStreamer {
    constructor(processId) {
        streamerInstances.set(processId, this);
        this.processId = processId;
        this.currentFrame = 0;
        this.isPlaying = true;
        this.init();
    }

    init() {
        this.setupDOM();
        this.setupEventListeners();
        this.startStreaming();
    }

    setupDOM() {
        // 创建视频容器
        this.videoContainer = document.createElement('div');
        this.videoContainer.className = 'video-container';
        this.videoContainer.innerHTML = `
            <div class="loading-overlay active">
                <div class="spinner"></div>
                <p>正在连接视频流...</p>
            </div>
            <img id="video-feed" class="processed-frame">
        `;

        // 插入到状态容器中
        const statusBox = document.querySelector('.video-stream-container');
        if (statusBox) {
            statusBox.innerHTML = ''; // 清空原有内容
            statusBox.appendChild(this.videoContainer); // 插入新容器
        }
    }

    setupEventListeners() {
        // 移除旧的点击监听器（避免重复绑定）
        this.videoContainer.removeEventListener('click', this.togglePlayback);
        
        // 使用箭头函数保持this指向
        this.togglePlayback = () => {
            console.log('🎬 点击触发, isPlaying:', this.isPlaying);
            this.isPlaying = !this.isPlaying;
            
            const overlay = this.videoContainer.querySelector('.loading-overlay');
            const videoElement = this.videoContainer.querySelector('#video-feed');
            
            if (this.isPlaying) {
                // 播放状态
                overlay.classList.remove('paused');
                overlay.innerHTML = `
                    <div class="spinner"></div>
                    <p>恢复播放...</p>
                `;
                this.startStreaming();
            } else {
                // 暂停状态
                overlay.classList.add('paused');
                overlay.innerHTML = `
                    <i class="bi bi-pause-fill"></i>
                    <p>已暂停（点击继续）</p>
                `;
            }
            
            // 添加/移除暂停样式到视频元素
            videoElement.classList.toggle('paused', !this.isPlaying);
        };
    
        // 绑定新监听器
        this.videoContainer.addEventListener('click', this.togglePlayback);
        console.log('事件监听器已初始化');
    }
    

    async startStreaming() {
        console.log('开始视频流处理:', this.processId);
        try {
            console.log('🔄 轮询状态，当前帧:', this.currentFrame);
            const status = await this.fetchStatus();
            
            if (status.ready) {
                this.onAnalysisComplete();
                return;
            }

            if (status.processed_frames >= this.currentFrame) {
                console.log('🆕 有新帧，准备更新');
                this.currentFrame = status.processed_frames;
                await this.updateFrame();
                this.showVideoFrame();
            }

            // 继续轮询
            if (this.isPlaying) {
                setTimeout(() => this.startStreaming(), 5000);
            }
        } catch (error) {
            console.error('视频流错误:', error);
            setTimeout(() => this.startStreaming(), 1000);
        }
    }

    async fetchStatus() {
        
        const response = await fetch(`/status/${this.processId}`, {
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        });
        console.log('请求状态:', response.json().processed_frames);

        if (!response.ok) throw new Error('状态请求失败');
        return response.json();
    }

    async updateFrame() {
        const img = document.getElementById('video-feed');
        // if (!img) return;
    
        // 确保URL格式与后端路由完全匹配
        const frameUrl = `/frame/${this.processId}/${this.currentFrame}?t=${Date.now()}`;
        console.log('请求帧:', frameUrl);  // 调试输出
    
        return new Promise((resolve) => {
            img.onload = () => {
                img.style.opacity = 1;  // 显示图像
                resolve();
            };
            img.onerror = () => {
                console.warn(`帧 ${this.currentFrame} 加载失败`);
                img.style.opacity = 0;  // 隐藏失败图像
                resolve();
            };
            img.src = frameUrl;
        });
    }
    

    showVideoFrame() {
        const loader = this.videoContainer.querySelector('.loading-overlay');
        if (loader) loader.classList.remove('active');
    }

    onAnalysisComplete() {
        const loader = this.videoContainer.querySelector('.loading-overlay');
        if (loader) {
            loader.innerHTML = `
                <div class="completed-message">
                    <i class="bi bi-check-circle"></i>
                    <p>分析完成！</p>
                </div>
            `;
        }
        
        // 3秒后刷新页面显示下载按钮
        setTimeout(() => window.location.reload(), 3000);
    }
}

// 页面初始化
document.addEventListener('DOMContentLoaded', () => {
    console.log('VideoStreamer class:', typeof VideoStreamer); 
    // 初始化上传页面功能
    if (document.getElementById('upload-form')) {
        new VideoUploader();
    }
    
    // 初始化状态页面功能
    const statusBox = document.querySelector('.status-box');
    if (statusBox) {
        const processId = statusBox.dataset.processId;
        if (processId) {
            new VideoStreamer(processId);
        }
    }
});
