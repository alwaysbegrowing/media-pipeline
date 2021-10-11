#!/bin/bash
mkdir -p logs
cd lambdas/mobile_export/combine
echo "FINAL_BUCKET=test" > docker.env
docker build -t combiner-test .
docker run --name "combiner-test" -d -p 9000:8080 --env-file docker.env combiner-test
python ../../../scripts/post.py "http://localhost:9000/2015-03-31/functions/function/invocations" ../../../events/combineEvent.json > ../../../logs/combiner.json
docker kill combiner-test
docker rm combiner-test
cd ../../..