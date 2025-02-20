# Docker 基底映像：AWS 提供的 Lambda Python 3.9
FROM public.ecr.aws/lambda/python:3.9

# 將 requirements.txt 複製進容器
COPY requirements.txt  .

# 安裝 Python 套件 (包含 ortools)
RUN  pip3 install --no-cache-dir -r requirements.txt

# 將專案檔案複製到容器 /var/task (Lambda 預設工作目錄)
COPY . /var/task/

# 告訴 Lambda，執行時要呼叫 "app.handler" 這個 Python 函式作為入口
CMD [ "lambda.handler" ]