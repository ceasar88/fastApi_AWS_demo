FROM public.ecr.aws/lambda/python:3.9

# Copy over source code
COPY . ${LAMBDA_TASK_ROOT}

# Install dependencies
RUN pip install -r ./requirements.txt \
    && pip install -r ./requirements-dev.txt \
    && pip install --editable .

# Launch lambda handler
CMD [ "functions.app.handler" ]
