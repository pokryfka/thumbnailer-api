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
	      AuthClientId=${AUTH_CLIENT_ID} \
	aws cloudformation describe-stacks \
    	--stack-name ${STACK_NAME} --query 'Stacks[].Outputs'

.PHONY: logs
logs:
	sam logs -n FacebookAuthFunction --stack-name ${STACK_NAME} --tail

.PHONY: test
test-th:
	curl -H "Accept: image/jpg" \
	  http://localhost:3000/thumbnailer/thumbnail/URI/long-edge/200

.PHONY: test
test-fit:
	curl -H "Accept: image/jpg" \
	  http://localhost:3000/thumbnailer/fit/URI/width/200/height/100

.PHONY: local
local: build
	sam local start-api
