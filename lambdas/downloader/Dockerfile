FROM ghcr.io/pillargg/ffmpeg-lambda-base:latest

COPY . .
RUN chmod +x ./entrypoint.sh

RUN pip3 install --no-cache-dir --upgrade pip
RUN pip3 install --no-cache-dir -r requirements.txt
WORKDIR /
ENTRYPOINT [ "./entrypoint.sh" ]
CMD ["main.handler"]
