import asyncio
import os
from flask import Flask, request, jsonify, render_template_string
import holehe

app = Flask(__name__)

# ====== HTML TEMPLATE (nhúng trực tiếp) ======
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Email Checker - Truy vết ứng dụng đã đăng ký</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        body {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh; display: flex; justify-content: center; align-items: center;
            padding: 20px; flex-direction: column;
        }
        .container {
            background: white; border-radius: 20px; padding: 40px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.2); width: 100%; max-width: 600px; text-align: center;
        }
        header h1 { font-size: 2.5rem; color: #333; margin-bottom: 10px; }
        .subtitle { color: #666; margin-bottom: 30px; font-size: 1.1rem; }
        .search-box { display: flex; gap: 10px; margin-bottom: 30px; position: relative; }
        #emailInput {
            flex: 1; padding: 15px 20px; border: 2px solid #e0e0e0; border-radius: 50px;
            font-size: 1rem; outline: none; transition: border-color 0.3s;
        }
        #emailInput:focus { border-color: #667eea; }
        #checkBtn {
            padding: 15px 30px; background: #667eea; color: white; border: none;
            border-radius: 50px; font-size: 1rem; font-weight: bold; cursor: pointer; transition: background 0.3s;
        }
        #checkBtn:hover { background: #5a67d8; }
        #checkBtn:disabled { background: #aaa; cursor: not-allowed; }
        .spinner {
            position: absolute; right: 160px; top: 50%; transform: translateY(-50%);
            width: 30px; height: 30px; border: 4px solid #f3f3f3; border-top: 4px solid #667eea;
            border-radius: 50%; animation: spin 1s linear infinite;
        }
        @keyframes spin {
            0% { transform: translateY(-50%) rotate(0deg); }
            100% { transform: translateY(-50%) rotate(360deg); }
        }
        .result {
            background: #f8f9fa; border-radius: 15px; padding: 20px; text-align: left;
        }
        .result h2 { font-size: 1.5rem; color: #333; margin-bottom: 10px; }
        .summary { color: #555; margin-bottom: 20px; font-size: 1.1rem; }
        .service-list { display: flex; flex-wrap: wrap; gap: 10px; }
        .service-tag {
            background: white; padding: 8px 15px; border-radius: 20px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1); font-size: 0.95rem; color: #333;
            display: inline-flex; align-items: center; gap: 5px;
        }
        .service-tag::before { content: "✅"; font-size: 0.9rem; }
        .error {
            background: #ffebee; color: #c62828; padding: 15px; border-radius: 10px;
            margin-top: 20px; font-weight: bold;
        }
        footer { margin-top: 20px; color: white; text-align: center; font-size: 0.9rem; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🔍 Email Checker</h1>
            <p class="subtitle">Nhập Gmail để kiểm tra các ứng dụng/dịch vụ mà email này đã đăng ký</p>
        </header>

        <div class="search-box">
            <input type="email" id="emailInput" placeholder="Nhập địa chỉ Gmail..." required>
            <button id="checkBtn">Kiểm tra</button>
            <div class="spinner" id="spinner" style="display: none;"></div>
        </div>

        <div class="result" id="result" style="display: none;">
            <h2>Kết quả cho: <span id="resultEmail"></span></h2>
            <p class="summary" id="summary"></p>
            <div class="service-list" id="serviceList"></div>
        </div>

        <div class="error" id="error" style="display: none;"></div>
    </div>

    <footer>
        <p>⚠️ Kết quả dựa trên dữ liệu công khai và có thể không chính xác 100%.</p>
    </footer>

    <script>
        const emailInput = document.getElementById('emailInput');
        const checkBtn = document.getElementById('checkBtn');
        const spinner = document.getElementById('spinner');
        const resultDiv = document.getElementById('result');
        const resultEmail = document.getElementById('resultEmail');
        const summary = document.getElementById('summary');
        const serviceList = document.getElementById('serviceList');
        const errorDiv = document.getElementById('error');

        checkBtn.addEventListener('click', async () => {
            const email = emailInput.value.trim();
            if (!email) {
                showError('Vui lòng nhập địa chỉ email!');
                return;
            }
            if (!/^\\S+@\\S+\\.\\S+$/.test(email)) {
                showError('Email không hợp lệ!');
                return;
            }

            hideError();
            resultDiv.style.display = 'none';
            checkBtn.disabled = true;
            spinner.style.display = 'block';

            try {
                const response = await fetch('/api/check-email', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email: email })
                });
                const data = await response.json();
                if (!response.ok) throw new Error(data.error || 'Có lỗi xảy ra');
                displayResult(data);
            } catch (err) {
                showError(err.message || 'Không thể kết nối đến server.');
            } finally {
                checkBtn.disabled = false;
                spinner.style.display = 'none';
            }
        });

        function displayResult(data) {
            resultEmail.textContent = data.email;
            summary.textContent = `Đã tìm thấy ${data.found_count} dịch vụ trong tổng số ${data.total_checked} dịch vụ được kiểm tra.`;
            serviceList.innerHTML = '';
            if (data.found_services.length === 0) {
                serviceList.innerHTML = '<p>Không tìm thấy dịch vụ nào khớp.</p>';
            } else {
                data.found_services.forEach(service => {
                    const tag = document.createElement('span');
                    tag.className = 'service-tag';
                    tag.textContent = service;
                    serviceList.appendChild(tag);
                });
            }
            resultDiv.style.display = 'block';
        }

        function showError(message) {
            errorDiv.textContent = message;
            errorDiv.style.display = 'block';
        }
        function hideError() {
            errorDiv.style.display = 'none';
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/check-email', methods=['POST'])
def check_email():
    data = request.get_json()
    if not data or 'email' not in data:
        return jsonify({"error": "Thiếu email"}), 400

    email = data['email'].strip().lower()
    if '@' not in email or '.' not in email:
        return jsonify({"error": "Email không hợp lệ"}), 400

    try:
        modules = holehe.get_functions()

        async def run_checks():
            tasks = [module(email) for module in modules]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            output = []
            for module, result in zip(modules, results):
                if isinstance(result, Exception):
                    output.append({"name": module.__name__, "exists": False, "error": str(result)})
                else:
                    output.append({
                        "name": module.__name__,
                        "exists": result.get("exists", False),
                        "emailrecovery": result.get("emailrecovery", None),
                        "phoneNumber": result.get("phoneNumber", None),
                        "others": result.get("others", None)
                    })
            return output

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        results = loop.run_until_complete(run_checks())
        loop.close()

        found_services = [r for r in results if r.get('exists') is True]

        return jsonify({
            "email": email,
            "total_checked": len(results),
            "found_count": len(found_services),
            "found_services": [r['name'] for r in found_services],
            "details": results
        })

    except Exception as e:
        return jsonify({"error": f"Lỗi khi kiểm tra: {str(e)}"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
