PROJECT=flying-data-mule


adanet-glider:
	docker compose -p ${PROJECT} -f ./stacks/adanet.yaml --env-file ./stacks/env-real.yaml up glider-source

adanet-glider-simulated:
	docker compose -p ${PROJECT} -f ./stacks/adanet.yaml --env-file ./stacks/env-simulated.yaml up glider-source

adanet-drone-glider:
	docker compose -p ${PROJECT} -f ./stacks/adanet.yaml --env-file ./stacks/env-real.yaml up drone-glider

adanet-drone-football:
	docker compose -p ${PROJECT} -f ./stacks/adanet.yaml --env-file ./stacks/env-real.yaml up drone-football

adanet-drone:
	docker compose -p ${PROJECT} -f ./stacks/adanet.yaml --env-file ./stacks/env-real.yaml up drone-glider drone-football

adanet-football-sink:
	docker compose -p ${PROJECT} -f ./stacks/adanet.yaml --env-file ./stacks/env-real.yaml up football-sink

adanet-football-drone:
	docker compose -p ${PROJECT} -f ./stacks/adanet.yaml --env-file ./stacks/env-real.yaml up football-drone

adanet-football-toughbook:
	docker compose -p ${PROJECT} -f ./stacks/adanet.yaml --env-file ./stacks/env-real.yaml up football-toughbook

adanet-football:
	docker compose -p ${PROJECT} -f ./stacks/adanet.yaml --env-file ./stacks/env-real.yaml up football-drone football-toughbook

adanet-toughbook-sink:
	docker compose -p ${PROJECT} -f ./stacks/adanet.yaml --env-file ./stacks/env-real.yaml up toughbook-sink
