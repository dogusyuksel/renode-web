.PHONY: setup-vcan run-in-docker run-in-wsl update-mcu-list

setup-vcan:
	@if ip link show dev vcan0 &> /dev/null; then \
		echo "VCAN0 already configured"; \
	else \
		sudo ip link add dev vcan0 type vcan && \
		sudo ip link set up vcan0 && \
		sudo ifconfig vcan0 up; \
	fi
	@if ip link show dev vcan1 &> /dev/null; then \
		echo "VCAN1 already configured"; \
	else \
		sudo ip link add dev vcan1 type vcan && \
		sudo ip link set up vcan1 && \
		sudo ifconfig vcan1 up; \
	fi

run-in-docker: setup-vcan
	bash -c 'sudo git clean -fdX && find scripts -type f \( -name "*.sh" -o -name "makefile" -o -name "Makefile" -o -name "*.py" \) -exec dos2unix {} + && cd scripts && ./docker_ctl.sh -b -s -c "cd /workspace/scripts && ./setup_env.sh && cd /workspace/web && python3 app.py"'

run-in-wsl: setup-vcan
	bash -c 'sudo git clean -fdX && find scripts -type f \( -name "*.sh" -o -name "makefile" -o -name "Makefile" -o -name "*.py" \) -exec dos2unix {} + && sudo ln -sf "$$PWD" /workspace && cd /workspace/scripts && ./setup_env.sh && cd /workspace/web && sudo python3 app.py'

update-mcu-list-in-wsl:
	bash -c 'cd scripts && python3 mcu_data_generator.py'

update-mcu-list-in-docker:
	bash -c 'cd scripts && ./docker_ctl.sh -b -s -c "cd /workspace/scripts && python3 mcu_data_generator.py"'
