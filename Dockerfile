FROM python:3.11

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY financial_news_analyzer.py .

CMD ["python", "financial_news_analyzer.py"]
