FROM python:3.9


WORKDIR /app
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY . .

# EXPOSE 80

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8081", "--reload"]
