PROJECT=flying-data-mule


virtual-network:
	docker-compose -p ${PROJECT} -f ./stacks/virtual-network.yaml up

adanet-real:
	docker-compose -p ${PROJECT} -f ./stacks/adanet.yaml --env-file ./stacks/env-real.yaml up

adanet-simulated:
	docker-compose -p ${PROJECT} -f ./stacks/adanet.yaml --env-file ./stacks/env-simulated.yaml up

glider-in-range:
	@docker exec ${PROJECT}_ppp1_0_1 ip link set dev ppp0 up

glider-out-of-range:
	@docker exec ${PROJECT}_ppp1_0_1 ip link set dev ppp0 down

shore-in-range:
	@docker exec ${PROJECT}_ppp1_2_1 ip link set dev ppp1 up

shore-out-of-range:
	@docker exec ${PROJECT}_ppp1_2_1 ip link set dev ppp1 down



show-network-configuration:
	@echo "- Connection 1 -----------------------------------------------------------------------"
	@docker exec ppp00 tc class show dev ppp0
	@docker exec ppp00 tc qdisc show dev ppp0
	@echo "-------"
	@docker exec ppp01 tc class show dev ppp0
	@docker exec ppp01 tc qdisc show dev ppp0
	@echo "- Connection 2 -----------------------------------------------------------------------"
	@docker exec ppp10 tc class show dev ppp0
	@docker exec ppp10 tc qdisc show dev ppp0
	@echo "-------"
	@docker exec ppp11 tc class show dev ppp0
	@docker exec ppp11 tc qdisc show dev ppp0
	@echo "--------------------------------------------------------------------------------------"
