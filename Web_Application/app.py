from flask import Flask, request, redirect, make_response, render_template_string
import base64, json

app = Flask(__name__)

LOGIN_PAGE = '''
<!DOCTYPE html>
<html>
<head>
<title>Business Application | Sign In</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: #1a1a2e; font-family: "Segoe UI", Arial, sans-serif;
         display: flex; justify-content: center; align-items: center;
         height: 100vh; }
  .card { background: #ffffff; width: 360px; padding: 40px;
          box-shadow: 0 8px 32px rgba(0,0,0,0.4); border-radius: 4px; }
  .brand { display: flex; align-items: center; gap: 10px; margin-bottom: 32px; }
  .brand-icon { width: 36px; height: 36px; background: #0057b8;
                border-radius: 4px; display: flex; align-items: center;
                justify-content: center; color: white; font-weight: bold;
                font-size: 18px; }
  .brand-name { font-size: 18px; font-weight: 600; color: #1a1a2e; }
  .brand-sub  { font-size: 11px; color: #888; }
  .field-label { font-size: 12px; color: #555; margin-bottom: 6px;
                 font-weight: 600; letter-spacing: 0.4px; }
  input { width: 100%; padding: 10px 12px; border: 1px solid #ddd;
          border-radius: 3px; font-size: 14px; margin-bottom: 18px;
          transition: border-color 0.2s; }
  input:focus { outline: none; border-color: #0057b8; }
  .btn { width: 100%; padding: 11px; background: #0057b8; color: white;
         border: none; border-radius: 3px; font-size: 14px; font-weight: 600;
         cursor: pointer; transition: background 0.2s; }
  .btn:hover { background: #0041a8; }
  .err { color: #cc0000; font-size: 12px; margin-bottom: 14px; min-height: 16px; }
  .footer { margin-top: 24px; text-align: center; font-size: 11px; color: #aaa; }
</style>
</head>
<body>
<div class="card">
  <div class="brand">
    <div class="brand-icon">B</div>
    <div>
      <div class="brand-name">Business Application</div>
      <div class="brand-sub">Enterprise Portal v4.2</div>
    </div>
  </div>
  <div class="field-label">Username</div>
  <input type="text" id="u" placeholder="Enter username" autocomplete="username"/>
  <div class="field-label">Password</div>
  <input type="password" id="p" placeholder="Enter password"
         autocomplete="current-password"/>
  <div class="err" id="err"></div>
  <button class="btn" onclick="doLogin()">Sign In</button>
  <div class="footer">© 2024 Business Application Suite. All rights reserved.</div>
</div>
<script>
function doLogin() {
    document.getElementById('err').innerText = '';
    fetch('/login', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            username: document.getElementById('u').value,
            password: document.getElementById('p').value
        })
    })
    .then(r => r.json())
    .then(d => {
        if (d.success) window.location = '/dashboard';
        else document.getElementById('err').innerText = d.error || 'Sign in failed';
    })
    .catch(() => {
        document.getElementById('err').innerText = 'Connection error. Try again.';
    });
}
document.addEventListener('keydown', e => { if (e.key === 'Enter') doLogin(); });
</script>
</body>
</html>
'''

DASHBOARD = '''
<!DOCTYPE html>
<html>
<head>
<title>Business Application | Dashboard</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: #f4f6f9; font-family: "Segoe UI", Arial, sans-serif; }
  .topbar { background: #0057b8; color: white; padding: 0 24px;
            height: 52px; display: flex; justify-content: space-between;
            align-items: center; box-shadow: 0 2px 8px rgba(0,0,0,0.2); }
  .topbar-left { display: flex; align-items: center; gap: 10px; }
  .brand-icon { width: 28px; height: 28px; background: white; border-radius: 3px;
                display: flex; align-items: center; justify-content: center;
                color: #0057b8; font-weight: bold; font-size: 14px; }
  .brand-name { font-size: 15px; font-weight: 600; }
  .topbar-right { display: flex; align-items: center; gap: 16px; font-size: 13px; }
  .user-badge { background: rgba(255,255,255,0.15); padding: 4px 12px;
                border-radius: 12px; font-size: 12px; }
  .logout-btn { background: transparent; border: 1px solid rgba(255,255,255,0.5);
                color: white; padding: 5px 14px; cursor: pointer; font-size: 12px;
                border-radius: 3px; font-weight: 600; }
  .logout-btn:hover { background: rgba(255,255,255,0.15); }
  .content { padding: 40px; }
  .welcome { background: white; padding: 28px; border-radius: 4px;
             border-left: 4px solid #0057b8; max-width: 620px;
             box-shadow: 0 1px 4px rgba(0,0,0,0.08); }
  .welcome h2 { color: #1a1a2e; margin-bottom: 10px; font-size: 18px; }
  .welcome p  { color: #555; font-size: 14px; line-height: 1.6; }
  .meta { margin-top: 18px; padding-top: 14px; border-top: 1px solid #eee;
          font-size: 11px; color: #999; display: flex; gap: 24px; }
</style>
</head>
<body>
<div class="topbar">
  <div class="topbar-left">
    <div class="brand-icon">B</div>
    <div class="brand-name">Business Application</div>
  </div>
  <div class="topbar-right">
    <span class="user-badge">{{ user }}</span>
    <form action="/logout" method="post" style="margin:0;">
      <button class="logout-btn" type="submit">Sign Out</button>
    </form>
  </div>
</div>
<div class="content">
  <div class="welcome">
    <h2>Welcome back, {{ user }}</h2>
    <p>You are signed into the Business Application Enterprise Portal.
       Your session is active and authenticated.</p>
    <div class="meta">
      <span>System: PROD</span>
      <span>Client: 100</span>
      <span>Last login: today</span>
    </div>
  </div>
</div>
</body>
</html>
'''

USERS = {
    'jdoe':  'Summer2024!',
    'admin': 'P@ssw0rd123'
}

@app.route('/')
def index():
    return render_template_string(LOGIN_PAGE)

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    u = data.get('username', '')
    p = data.get('password', '')
    if USERS.get(u) == p:
        token = base64.b64encode(json.dumps({'user': u, 'pass': p}).encode()).decode()
        resp  = make_response({'success': True})
        resp.set_cookie('session_token', token, httponly=False, max_age=86400)
        return resp
    return {'success': False, 'error': 'Invalid username or password'}

@app.route('/dashboard')
def dashboard():
    token = request.cookies.get('session_token', '')
    try:
        data = json.loads(base64.b64decode(token))
        return render_template_string(DASHBOARD, user=data['user'])
    except Exception:
        return redirect('/')

@app.route('/logout', methods=['POST'])
def logout():
    resp = make_response(redirect('/'))
    resp.delete_cookie('session_token')
    return resp

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
