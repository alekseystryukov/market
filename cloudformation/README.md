# Cloudformation templates for AWS


## Deploy common resources

```shell

REGION=eu-central-1
AdministratorEmailAddress=aleksey.stryukov@gmail.com



aws cloudformation create-stack \
  --region ${REGION} \
  --profile admin \
  --stack-name common-stack \
  --capabilities CAPABILITY_IAM \
  --template-body "file://./cloudformation/templates/01_common.yaml" \
  --parameters \
   ParameterKey=AdministratorEmailAddress,ParameterValue=${AdministratorEmailAddress}



aws cloudformation update-stack \
  --region ${REGION} \
  --profile admin \
  --stack-name common-stack \
  --capabilities CAPABILITY_IAM \
  --template-body "file://./cloudformation/templates/01_common.yaml" \
  --parameters \
   ParameterKey=AdministratorEmailAddress,ParameterValue=${AdministratorEmailAddress}
   
```


## VPC and RDS

```shell

DBUsername=suspender
DBPassword=zBObBgEAD6WtYFf



aws cloudformation create-stack \
  --profile admin \
  --stack-name base-vpc \
  --capabilities CAPABILITY_IAM \
  --template-body "file://./cloudformation/templates/00_vpc.yaml" \
  --parameters \
   ParameterKey=DBUsername,ParameterValue=${DBUsername} \
   ParameterKey=DBPassword,ParameterValue=${DBPassword} 



```