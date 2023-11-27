FROM python:3.8-slim
WORKDIR /Client
COPY . /Client/
RUN pip install --upgrade pip \
    && pip install -r requirements.txt
CMD ["python", "bot.py"]