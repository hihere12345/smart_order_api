如何运行该项目：
1. 确保8000端口未被占用。
2. 安装所需依赖：pip install -r requirements.txt
3. 运行服务：python manage.py runserver
4. 通过http://localhost:8000/admin登录管理后台查看数据。用户名：admin，密码：smartorder123
5. 或者可以通过http://127.0.0.1:8000/swagger/查看所有APIs以及请求参数
6. 或者将SmartOrder.postman_collection.json导入到postman中调用APIs