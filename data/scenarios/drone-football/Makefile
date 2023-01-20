PROJECT=drone-shore


virtual-network:
	docker compose -p ${PROJECT} -f ./stacks/virtual-network.yaml --env-file ./stacks/env-simulated.yaml up

adanet-drone-simulated:
	docker compose -p ${PROJECT} -f ./stacks/adanet.yaml --env-file ./stacks/env-simulated.yaml up drone

adanet-drone:
	docker compose -p ${PROJECT} -f ./stacks/adanet.yaml --env-file ./stacks/env-real.yaml up drone

adanet-shore:
	docker compose -p ${PROJECT} -f ./stacks/adanet.yaml --env-file ./stacks/env-real.yaml up shore

adanet-simulated-isolated:
	docker compose -p ${PROJECT} -f ./stacks/adanet.yaml --env-file ./stacks/env-simulated-isolated.yaml up

drone-in-range:
	@docker exec ${PROJECT}_ppp00_1 ip link set dev ppp0 up

drone-out-of-range:
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
