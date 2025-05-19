// static/js/app.js
document.addEventListener('DOMContentLoaded', function() {
    // 状态页自动刷新
    if (document.getElementById('progress-container')) {
        const processId = window.location.pathname.split('/').pop();
        let progress = 0;
        
        const updateProgress = () => {
            fetch(`/progress/${processId}`)
                .then(res => res.json())
                .then(data => {
                    const progressBar = document.getElementById('progress-bar');
                    progressBar.style.width = `${data.progress}%`;
                    progressBar.textContent = `${data.progress}%`;
                    
                    if (data.ready) {
                        document.getElementById('status-text').textContent = "分析完成！";
                        document.getElementById('result-section').style.display = 'block';
                        document.getElementById('result-video').src = 
                            `/output/${processId}/output.mp4?t=${Date.now()}`;
                        
                        // 加载统计数据
                        if (data.stats) {
                            const list = document.getElementById('stats-list');
                            list.innerHTML = Object.entries(data.stats)
                                .map(([key, val]) => `
                                    <li class="list-group-item d-flex justify-content-between">
                                        <span>${key}</span>
                                        <span class="badge bg-primary">${val}</span>
                                    </li>
                                `).join('');
                        }
                    } else {
                        setTimeout(updateProgress, 2000);
                    }
                });
        };
        
        updateProgress();
    }

    // 视频预览功能
    window.previewVideo = function(input) {
        const preview = document.getElementById('video-preview');
        const file = input.files[0];
        const url = URL.createObjectURL(file);
        
        preview.innerHTML = `
            <video controls class="rounded" style="max-width: 100%; max-height: 300px;">
                <source src="${url}" type="${file.type}">
                您的浏览器不支持视频预览
            </video>
        `;
    };
});
