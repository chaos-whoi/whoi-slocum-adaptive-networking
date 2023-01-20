PROJECT=glider-drone


virtual-network:
	docker compose -p ${PROJECT} -f ./stacks/virtual-network.yaml --env-file ./stacks/env-simulated.yaml up

adanet-glider-simulated:
	docker compose -p ${PROJECT} -f ./stacks/adanet.yaml --env-file ./stacks/env-simulated.yaml up glider

adanet-glider:
	docker compose -p ${PROJECT} -f ./stacks/adanet.yaml --env-file ./stacks/env-real.yaml up glider

adanet-drone:
	docker compose -p ${PROJECT} -f ./stacks/adanet.yaml --env-file ./stacks/env-real.yaml up drone

adanet-simulated-isolated:
	docker compose -p ${PROJECT} -f ./stacks/adanet.yaml --env-file ./stacks/env-simulated-isolated.yaml up

glider-in-range:
	@docker exec ${PROJECT}_ppp00_1 ip link set dev ppp0 up

glider-out-of-range:
	@docker exec ${PROJECT}_ppp00_1 ip link set dev ppp0 down


show-network-configuration:
	@echo "- Connection 1 -----------------------------------------------------------------------"
	@docker exec ${PROJECT}_ppp00_1 tc class show dev ppp0
	@docker exec ${PROJECT}_ppp00_1 tc qdisc show dev ppp0
	@echo "-------"
	@docker exec ${PROJECT}_ppp01_1 tc class show dev ppp0
	@docker exec ${PROJECT}_ppp01_1 tc qdisc show dev ppp0
	@echo "- Connection 2 -----------------------------------------------------------------------"
	@docker exec ${PROJECT}_ppp10_1 tc class show dev ppp0
	@docker exec ${PROJECT}_ppp10_1 tc qdisc show dev ppp0
	@echo "-------"
	@docker exec ${PROJECT}_ppp11_1 tc class show dev ppp0
	@docker exec ${PROJECT}_ppp11_1 tc qdisc show dev ppp0
	@echo "--------------------------------------------------------------------------------------"
