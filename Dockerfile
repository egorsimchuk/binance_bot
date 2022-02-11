FROM python:3.8
ENV PYTHONPATH=/app
WORKDIR /app

COPY . .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r ./requirements.txt

CMD ["python","scripts/make_html_report.py"]
