FROM public.ecr.aws/bitnami/python:3.8-prod

RUN apt-get update && apt-get install --no-install-recommends -y build-essential ffmpeg \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY . .

RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN pip install awslambdaric

RUN apt-get purge build-essential -y && apt-get autoremove -y

WORKDIR /
ENTRYPOINT [ "python", "-m", "awslambdaric" ]
CMD ["main.handler"]