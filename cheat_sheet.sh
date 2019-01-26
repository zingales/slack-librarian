# Running link updated container

docker build -t amzlnx . && docker run --env-file .env -it amzlnx /bin/bash
docker build -t amzlnx . && docker run --env-file .env amzlnx

# deploying lambda
sam build --use-container && sam package     --output-template-file packaged.yaml     --s3-bucket zingales  && aws cloudformation deploy --template-file /Users/bellepeng/Projects/awsLibrarian/slackbot/packaged.yaml --stack-name awsLibrarian --capabilities CAPABILITY_IAM
