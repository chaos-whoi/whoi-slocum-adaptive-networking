PROJECT=glider-boat


virtual-network:
	docker compose -p ${PROJECT} -f ./stacks/virtual-network.yaml up

adanet-real:
	docker compose -p ${PROJECT} -f ./stacks/adanet.yaml --env-file ./stacks/env-real.yaml up

adanet-simulated:
	docker compose -p ${PROJECT} -f ./stacks/adanet.yaml --env-file ./stacks/env-simulated.yaml up

glider-in-range:
	@docker exec ${PROJECT}-ppp0-1 ip link set dev ppp0 up

glider-out-of-range:
	@docker exec ${PROJECT}-ppp0-1 ip link set dev ppp0 down

local-boat:
	docker compose -p ${PROJECT} -f ./stacks/adanet.yaml --env-file ./stacks/env-real.yaml up boat

duckiebot-as-glider:
	docker -H tcp://192.168.9.150:2375 compose -p ${PROJECT} -f ./stacks/adanet.yaml --env-file ./stacks/env-real.yaml up glider


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
