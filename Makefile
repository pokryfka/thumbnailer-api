TEMPLATE_FILE=.aws-sam/packaged.yaml

#TEST_API_URL="http://localhost:3000/thumbnailer"
#TEST_API_URL="https://zcp3bjft0k.execute-api.us-east-1.amazonaws.com/Prod/thumbnailer"
TEST_API_URL="https://d1t7lw12hvlvkf.cloudfront.net/thumbnailer"

#TEST_URI_PREFIX=""
#TEST_ENCODED_URI="s3%3A%2F%2Fmyx-auth-dev-picturesbucket-2rm0spux6ue7%2Fprofile%2Ffb%2Ffb485679945593934.jpg"

TEST_URI_PREFIX="s3://myx-auth-dev-picturesbucket-2rm0spux6ue7/profile/fb/"
TEST_ENCODED_URI="fb485679945593934.jpg"

.PHONY: clean
clean:
	rm -rf .aws-sam

.PHONY: build
build:
	sam build

.PHONY: package
package: build
	sam package \
	    --output-template-file ${TEMPLATE_FILE} \
	    --s3-bucket ${PACKAGE_BUCKET}

.PHONY: deploy
deploy: package
	sam deploy \
	    --template-file ${TEMPLATE_FILE} \
	    --stack-name ${STACK_NAME} \
		--capabilities CAPABILITY_IAM
	aws cloudformation describe-stacks \
    	--stack-name ${STACK_NAME} --query 'Stacks[].Outputs'

.PHONY: logs
logs:
	sam logs -n ThumbnailerFunction --stack-name ${STACK_NAME} --tail

.PHONY: test-info
test-info:
	#curl ${TEST_API_URL}/info/${TEST_ENCODED_URI}
	http ${TEST_API_URL}/info/${TEST_ENCODED_URI} Uri-Prefix:${TEST_URI_PREFIX}

.PHONY: test-th
test-th:
	#curl -H "Accept: image/jpg" \
	#  ${TEST_API_URL}/thumbnail/${TEST_ENCODED_URI}/long-edge/666 > test.jpg
	http -v -d ${TEST_API_URL}/thumbnail/${TEST_ENCODED_URI}/long-edge/666 Accept:image/jpg Uri-Prefix:${TEST_URI_PREFIX}

.PHONY: test-fit
test-fit:
	#curl -H "Accept: image/jpg" \
	#  ${TEST_API_URL}/fit/${TEST_ENCODED_URI}/width/200/height/100 > test.jpg
	http -v -d ${TEST_API_URL}/fit/${TEST_ENCODED_URI}/width/200/height/100 Accept:image/jpg Uri-Prefix:${TEST_URI_PREFIX}

.PHONY: local
local: build
	sam local start-api
