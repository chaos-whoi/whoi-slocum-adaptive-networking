PROJECT=glider-drone-rosbag


virtual-network:
	docker compose -p ${PROJECT} -f ./stacks/virtual-network.yaml --env-file ./stacks/env.yaml up

adanet-glider:
	docker compose -p ${PROJECT} -f ./stacks/adanet.yaml --env-file ./stacks/env.yaml up roscore rosbag glider

adanet-drone:
	docker compose -p ${PROJECT} -f ./stacks/adanet.yaml --env-file ./stacks/env.yaml up drone

glider-in-range:
	@docker exec ${PROJECT}_ppp00_1 ip link set dev ppp0 up

glider-out-of-range:
	@docker exec ${PROJECT}_ppp00_1 ip link set dev ppp0 down
