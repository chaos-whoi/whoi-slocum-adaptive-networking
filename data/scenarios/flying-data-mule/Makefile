PROJECT=flying-data-mule


virtual-network:
	docker-compose -p ${PROJECT} -f ./stacks/virtual-network.yaml up

adanet:
	docker-compose -p ${PROJECT} -f ./stacks/adanet.yaml up



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
