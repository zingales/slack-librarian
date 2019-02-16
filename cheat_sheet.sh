# Running link updated container

docker build -t amzlnx . && docker run --env-file .env -it amzlnx /bin/bash
docker build -t amzlnx . && docker run --name linker-01 --env-file .env -d amzlnx && docker logs -f linker-01

# deploying lambda
sam build --use-container && sam package     --output-template-file packaged.yaml     --s3-bucket zingales  && aws cloudformation deploy --template-file /Users/bellepeng/Projects/awsLibrarian/slackbot/packaged.yaml --stack-name awsLibrarian --capabilities CAPABILITY_IAM
