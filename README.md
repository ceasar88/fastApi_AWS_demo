# Sygno FastAPI demo
![Architecture](diagram.png)
This project implements an API with the following functionality:
- Two POST endpoints for read and write
- Authentication to allow for different roles between the "write" endpoint and the "read" endpoints

### Some FastAPI advantages
- It is indeed fast
![Speed](speed.png)
- Built-in concurrency with aysnc execution of requests which also improves speed
- Built-in documentation
- Pydantic support and data validation
### Project Dependencies

- python 3.10 or higher
- pip
- virtualenv
- aws cli & cdk

### Project Structure and Overview

The project is structured to allow for building and deployment as a docker backed AWS lambda function or to package up lambda layer zip file.  Under the hood, the lambda
handler is written as a FastAPI app, and it uses [Mangum](https://mangum.io/) an adapter for running ASGI applications in AWS Lambda to handle API Gateway, ALB, and Lambda@Edge events.

```bash
├── README.md                   # This file
├── api                         # API service
│   ├── infrastructure.py       # CDK definition for the API Construct
│   └── src
│       ├── Dockerfile          # Dockerfile to build the API image
│       ├── functions           # Contains Lambda handler
│       ├── sygno_api          # Package code for the API including AWS utility and event logging methods
├── database                    # API's dynamodb table
│   ├── infrastructure.py       # CDK definition for API dynamodb table Construct
├── app.py                      # Core CDK file for deployment
├── constants.py                # Functions and derived values to augment CDK context values
├── cdk.json                    # CDK config
├── permission_boundary.py      # CDK permissions boundary
├── requirements-dev.txt        # Dev requirements
├── requirements.txt            # Requirements for running CDK
├── scripts                     # Utility scripts
└── tests                       # Unit tests
└── key.csv                     # AWS configure keys
└── startup.sh                  # shell script to stand up API in browser
```


### Running FastAPI in local browser

##### AWS Configure
First, we have to configure the aws cli to have access to aws resources.


Open a terminal and run command: 
  
`aws configure`

You will be prompted for the following:
```commandline
AWS Access Key ID: AKIA25H3MEGKJFOSGYIS
AWS Secret Access Key: 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
Default region name: us-west-1
```

##### Stand up the fastAPI server
In the project home directory, open terminal and run the following commands(see below for windows commands):

```commandline
chmod u+x startup.sh
./startup.sh
```
Or manually with:

```commandline
python3 -m venv ./venv
source ./venv/bin/activate
cd api/src
pip install -r requirements.txt
pip install --editable .
python functions/app.py
```
##### For windows:

```commandline
python -m venv .\venv
venv\Scripts\activate
cd api\src
pip install -r requirements.txt
pip install --editable .
python functions\app.py
```

Point a web browser to http://localhost:5005/docs to see the Swagger documentation. You can make requests via the documentation,
or you can send CURL commands like:
```
curl -X 'POST' \
  'http://localhost:5005/source/expose' \
  -H 'accept: application/json' \
  -H 'x-api-key: A39658387A1C13B94E78A7F37BDCB' \
  -H 'Content-Type: application/json' \
  -d '{
  "type": "latest"
}'
```

#### Manual CDK Deploy from command line

Ensure CDK v2 and AWS CLI tools are installed

The following will synthesize and deploy the stack.  By default the deployment environment
is `dev`.
```commandline
cdk synth
cdk bootstrap
cdk deploy
```
After the deployment, the API and other resources should be set up and accessible through aws. 
One could run the api in podman or have another aws resource access it through AWS API gateway.


Now you should be able to go to cloudformation and look at the stack resources (APIgateway, lambda and table)


#### Api Table Schema
```
{
    id: str                 # "action"
    sk: str                 # timestamp
    event_time: str         # timestamp same as sk
    name: str               # record name
    user_id: Optional[str]  # api_key used to read or write
    data: Optional[Dict]    # data like configuration parameters, request or response data
}
```

#### Api End Points
Write Endpoint:
```
POST /source/write_raw

Request:
{
  data: {}                   # raw data
}

Response:
{
  status: code               # status code
  description: str           # description of status
  data: {}                   # response data
}

api_keys:
[
    "CC519BF33D11DBFB46B8787BECF96",
    "584F6E17FADB24258E75EF645EAA1",
]

```

Read Endpoint:
```
POST /source/expose

Request:
{
  type: str                  # The type of data to expose: latest | 24h_devt| 24_average | 7d_devt | 7d_average
}

Response:
{
  status: code               # status code
  description: str           # description of status
  data: {}                   # response data
}

api_keys:
[
    "A39658387A1C13B94E78A7F37BDCB",
    "513792269572187F57A1FFBC8DC3D",
]

```
