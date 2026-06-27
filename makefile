run-in-docker:
	bash -c 'sudo git clean -fdX && find scripts -type f \( -name "*.sh" -o -name "makefile" -o -name "Makefile" -o -name "*.py" \) -exec dos2unix {} + && cd scripts && ./setup_env.sh && ./docker_ctl -b -s -c "cd web && python3 app.py"'

run-in-wsl:
	bash -c 'sudo git clean -fdX && find scripts -type f \( -name "*.sh" -o -name "makefile" -o -name "Makefile" -o -name "*.py" \) -exec dos2unix {} + && sudo ln -sf "$$PWD" /workspace && cd /workspace/scripts && ./setup_env.sh && cd /workspace/web && sudo python3 app.py'

update-mcu-list:
	bash -c 'find scripts -type f \( -name "*.sh" -o -name "makefile" -o -name "Makefile" -o -name "*.py" \) -exec dos2unix {} + && cd scripts && python3 mcu_data_generator.py'

