# If the first argument is "slow"...
ifeq (slow,$(firstword $(MAKECMDGOALS)))
  # use the rest as arguments for "slow"
  ARGS := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
  # first argument is the target
  SLOW_TARGET := $(wordlist 1,1,$(ARGS))
  # use the rest as arguments for "slow"
  SLOW_ARGS := $(wordlist 2,$(words $(ARGS)),$(ARGS))
  # ...and turn them into do-nothing targets
  $(eval $(ARGS):;@:)
endif

MACHINE=rpi
PPP_LOCAL_IP=10.0.0.1
PPP_LOCAL_DEV=/dev/ttyUSB0
PPP_REMOTE_IP=10.0.0.2
PPP_REMOTE_DEV=/dev/ttyUSB0
PPP_BAUD_RATE=115200
REMOTE_MACHINE=gliderpi.local
OUT_DIR=./out
COVERAGE_DIR=${OUT_DIR}/coverage
ROOT_DIR:=$(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))


slow:
	docker exec -it $(SLOW_TARGET) slow $(SLOW_ARGS)

run-echo-server:
	cpk run -L echo-server --name echo-server -M -- --net whoi --cap-add NET_ADMIN

run-echo-client:
	cpk run -L echo-client --name echo-client -M -- --net whoi --link echo-server --cap-add NET_ADMIN

run-bw-server-isolated:
	cpk run -L bw-server --name bw-server -M -- --net whoi --cap-add NET_ADMIN

run-bw-client-isolated:
	cpk run -L bw-client --name bw-client -M -- --net whoi --link bw-server --cap-add NET_ADMIN

run-bw-server:
	cpk run -L bw-server --name bw-server -M -- -p 5678:5678 --cap-add NET_ADMIN

run-bw-client:
	cpk run -L bw-client --name bw-client -M -- --link bw-server --cap-add NET_ADMIN

run-bw-client-remote:
	cpk run -H ${MACHINE} -L bw-client --name bw-client -M -s

setup-virtual-serial:
	sudo socat -d -d PTY,raw,echo=0,link=/dev/ttyV0 PTY,raw,echo=0,link=/dev/ttyV1

setup-ppp-local:
	# NOTE: this needs to run on the local computer, during testing this was a laptop connected to a Waveshare USB to RS232/485/TTL
	sudo pppd -detach ${PPP_LOCAL_DEV} ${PPP_BAUD_RATE} ${PPP_LOCAL_IP}:${PPP_REMOTE_IP} proxyarp local noauth debug nodetach dump nocrtscts passive persist

setup-ppp-remote:
	# NOTE: this needs to run on the remote computer, during testing this was a Raspberry Pi connected to a Waveshare USB to RS232/485/TTL
	ssh ubuntu@${REMOTE_MACHINE} -- sudo pppd -detach ${PPP_REMOTE_DEV} ${PPP_BAUD_RATE} ${PPP_REMOTE_IP}:${PPP_LOCAL_IP} proxyarp local noauth debug nodetach dump nocrtscts passive persist

virtual-network:
	docker-compose -p virtual-network -f ./stacks/virtual-network.yaml up

_network-control:
	docker-compose -p network-control -f ./stacks/network-control.yaml --env-file ./config/${NETWORK_CONFIG}.yaml up

network-control-ethernet-ethernet:
	$(MAKE) NETWORK_CONFIG=ethernet-ethernet _network-control

network-control-wifi-acoustic:
	$(MAKE) NETWORK_CONFIG=wifi-acoustic _network-control

network-control-wifi-wifi:
	$(MAKE) NETWORK_CONFIG=wifi-wifi _network-control

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

tests2:
	PYTHONPATH=${ROOT_DIR}/packages:${PYTHONPATH} \
		nosetests \
			--rednose \
			--immediate \
			--cover-html \
			--cover-html-dir=${COVERAGE_DIR} \
			--cover-tests \
			--with-coverage \
			--cover-package=adanet \
			--where=tests \
			-v \
			--nologcapture
