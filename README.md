# Market Project



## Update robot image

```shell
export $(grep -v '^#' .env | xargs)
aws ecr get-login-password --profile admin --region ${AWS_DEFAULT_REGION} | docker login --username AWS --password-stdin ${ECR_ROBOT_REPOSITORY_URL}

docker build ./robot/ -t ${ECR_ROBOT_REPOSITORY_URL}:latest

docker push $ECR_ROBOT_REPOSITORY_URL:latest
    
```