TEMPLATE_FILE=.aws-sam/packaged.yaml

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
		--capabilities CAPABILITY_IAM \
		--parameter-overrides \
			SentryDsn=${SENTRY_DSN}
	aws cloudformation describe-stacks \
    	--stack-name ${STACK_NAME} --query 'Stacks[].Outputs'

.PHONY: logs
logs:
	sam logs -n ThumbnailerFunction --stack-name ${STACK_NAME} --tail

.PHONY: test-info
test-info:
	http ${TEST_API_URL}/info/${TEST_ENCODED_URI} \
	  Uri-Prefix:${TEST_URI_PREFIX} X-Api-Key:${TEST_X_API_KEY}

.PHONY: test-th
test-th:
	http -v -d ${TEST_API_URL}/thumbnail/${TEST_ENCODED_URI}/long-edge/666 Accept:image/jpg \
	  Uri-Prefix:${TEST_URI_PREFIX} X-Api-Key:${TEST_X_API_KEY}

.PHONY: test-fit
test-fit:
	http -v -d ${TEST_API_URL}/fit/${TEST_ENCODED_URI}/width/200/height/100 Accept:image/jpg \
	  Uri-Prefix:${TEST_URI_PREFIX} X-Api-Key:${TEST_X_API_KEY}

.PHONY: local
local: build
	sam local start-api

.PHONY: style
style:
	black thumbnailer
