// static/js/app.js
// 通用功能
document.addEventListener('DOMContentLoaded', function() {
    // 初始化工具提示
    const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    [...tooltips].forEach(tooltip => new bootstrap.Tooltip(tooltip));
  
    // 表单提交处理
    document.querySelectorAll('.ajax-form').forEach(form => {
      form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(form);
        try {
          const response = await fetch(form.action, {
            method: 'POST',
            body: formData
          });
          handleResponse(await response.json());
        } catch (error) {
          showError('请求失败，请检查网络连接');
        }
      });
    });
  });
  
  function showError(message) {
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-danger';
    alertDiv.textContent = message;
    document.querySelector('#messages').appendChild(alertDiv);
  }