FROM python:3

WORKDIR /

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python setup.py bdist_wheel
RUN pip install $(ls dist/flaskr-*)

CMD waitress-serve --call 'flaskr:create_app'