docker build -t amzlnx . && docker run --env-file .env -it amzlnx /bin/bash
docker build -t amzlnx . && docker run --env-file .env amzlnx
