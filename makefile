run-in-docker:
	bash -c "sudo git clean -fdX && cd scripts && ./setup_env.sh && ./docker_ctl -b -s -c 'cd web && python3 app.py'"

run-in-wsl:
	bash -c 'sudo git clean -fdX && sudo ln -sf "$$PWD" /workspace && cd /workspace/scripts && ./setup_env.sh && cd /workspace/web && sudo python3 app.py'
