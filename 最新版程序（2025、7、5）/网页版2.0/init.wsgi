# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, 'D:/web_project/4/')
from sql_program import DatabaseManager, AuthService   
import urllib.parse

def application(environ, start_response):
    # 获取请求方法
    request_method = environ.get('REQUEST_METHOD', '')
    
    if request_method == 'POST' and environ['PATH_INFO'] == '/sign_in':
        try:
            content_length = int(environ.get('CONTENT_LENGTH', 0))
            post_data = environ['wsgi.input'].read(content_length).decode('utf-8')
            fields = urllib.parse.parse_qs(post_data)
            username = fields.get('username', [''])[0]
            password = fields.get('password', [''])[0]

            Db = DatabaseManager()
            auth = AuthService(Db)
            result = auth.login_user(username, password)

            if result['success'] == True:
                # 查询权限
                user_permission = None
                try:
                    with Db._get_connection() as conn:
                        cursor = conn.cursor(dictionary=True)
                        cursor.execute("SELECT permission FROM users WHERE user_id = %s", (result["user_id"],))
                        row = cursor.fetchone()
                        if row:
                            user_permission = row["permission"]
                except Exception:
                    user_permission = None

                with open('D:/web_project/4/html/main_web.html', 'r', encoding='utf-8') as f:
                    response_body = f.read()
                # 在页面末尾插入JS，保存user_id和permission到localStorage
                insert_js = f"""
<script>
    localStorage.setItem('currentUserId', '{result["user_id"]}');
    localStorage.setItem('currentUserPermission', '{user_permission or ""}');
</script>
"""
                # 如果main_web.html有</body>，插入到前面；否则直接加到最后
                if '</head>' in response_body:
                    response_body = response_body.replace('</head>', insert_js + '</head>')
                elif '<body>' in response_body:
                    response_body = response_body.replace('<body>', '<body>' + insert_js)
                else:
                    response_body = insert_js + response_body

                status = '200 OK'
                response_headers = [
                    ('Content-Type', 'text/html; charset=utf-8'),
                    ('Content-Length', str(len(response_body.encode('utf-8'))))
                ]

            else:
                with open('D:/web_project/4/html/sign_in_failed_web.html', 'r', encoding='utf-8') as f:
                    response_body = f.read()
                status = '200 OK'  
                response_headers = [
                    ('Content-Type', 'text/html; charset=utf-8'),
                    ('Content-Length', str(len(response_body.encode('utf-8'))))
                ]

        except Exception as e:
            response_body = f"服务器错误: {e}"
            status = '500 Internal Server Error'
            response_headers = [
                ('Content-Type', 'text/plain; charset=utf-8'),
                ('Content-Length', str(len(response_body.encode('utf-8'))))
            ]

    elif request_method == 'POST' and environ['PATH_INFO'] == '/sign_up':
        try:
            content_length = int(environ.get('CONTENT_LENGTH', 0))
            post_data = environ['wsgi.input'].read(content_length).decode('utf-8')
            fields = urllib.parse.parse_qs(post_data)
            username = fields.get('username', [''])[0]
            password = fields.get('password', [''])[0]
            role = fields.get('role', ['student'])[0]
            teacher_password = fields.get('teacherPassword', [''])[0]

            Db = DatabaseManager()
            auth = AuthService(Db)
            isteacher = (role == 'teacher')
            yanzheng = teacher_password if isteacher else None

            result = auth.register_user(username, password, isteacher=isteacher, yanzheng=yanzheng)

            if result['success'] == True:
                # 查询所有用户权限
                response_body = "注册成功！"
                status = '200 OK'
                response_headers = [
                    ('Content-Type', 'text/html; charset=utf-8'),
                    ('Content-Length', str(len(response_body.encode('utf-8'))))
                ]
            else:
                response_body = result['error']
                status = '200 OK'
            response_headers = [
                ('Content-Type', 'text/plain; charset=utf-8'),
                ('Content-Length', str(len(response_body.encode('utf-8'))))
            ]
        except Exception as e:
            response_body = f"服务器错误: {e}"
            status = '500 Internal Server Error'
            response_headers = [
                ('Content-Type', 'text/plain; charset=utf-8'),
                ('Content-Length', str(len(response_body.encode('utf-8'))))
            ]
    else:
        response_body = "408 Request Time-out"
        status = '408 Request Time-out'
        response_headers = [
            ('Content-Type', 'text/plain; charset=utf-8'),
            ('Content-Length', str(len(response_body.encode('utf-8'))))
        ]



    
    start_response(status, response_headers)
    
    return [response_body.encode('utf-8')]