FROM python:3-slim
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py app.py
COPY templates templates
COPY static static
CMD python app.py 0.0.0.0:5000
EXPOSE 5000