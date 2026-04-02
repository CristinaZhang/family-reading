#!/bin/bash

# 创建static目录
mkdir -p static

# 下载Swagger UI文件
echo "Downloading Swagger UI files..."
curl -o static/swagger-ui-bundle.js https://cdn.jsdelivr.net/npm/swagger-ui-dist@4/swagger-ui-bundle.js
curl -o static/swagger-ui.css https://cdn.jsdelivr.net/npm/swagger-ui-dist@4/swagger-ui.css
curl -o static/favicon-32x32.png https://cdn.jsdelivr.net/npm/swagger-ui-dist@4/favicon-32x32.png
curl -o static/redoc.standalone.js https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js

echo "Swagger UI files downloaded successfully!"

# 赋予执行权限
chmod +x static/swagger-ui-bundle.js
chmod +x static/redoc.standalone.js

echo "Static files are ready for use."
