# canvas-qti
Generate Canvas CTI zip archives as web app

## Install

```
poetry install
```

## Run test web server

```
export FLASK_APP=server.py
poetry run python -m flask run
```

## Run test web query

### Validate only
```
curl -i --data-binary '@data/test1.md' http://localhost:5000/validate
```

### Validate and download generated QTI zip archive
```
curl -v --output data/out2 --data-binary '@data/test1.md' http://localhost:5000/validate?generate
```
