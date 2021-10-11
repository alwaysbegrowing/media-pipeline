cd lambdas/downloader
# get all text after equal sign on the second line
AWS_ACCESS_KEY_ID=`/usr/bin/cat ~/.aws/credentials | awk 'NR==2 {print $3}'`
AWS_SECRET_ACCESS_KEY=`/usr/bin/cat ~/.aws/credentials | awk 'NR==3 {print $3}'`
echo "AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID" > docker.env
echo "AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY" >> docker.env
echo "AWS_REGION=us-east-1" >> docker.env
echo "AWS_DEFAULT_REGION=us-east-1" >> docker.env
echo "AWS_LAMBDA_FUNCTION_MEMORY=1024" >> docker.env
docker build -t downloader-test .
docker run --name "downloader-test" -d -p 9000:8080 --env-file docker.env downloader-test
python ../../scripts/post.py "http://localhost:9000/2015-03-31/functions/function/invocations" ../../events/downloadEvent.json > ../../logs/downloader.json
docker kill downloader-test
docker rm downloader-test
cd ../..