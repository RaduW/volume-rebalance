
all: config
.PHONY: all

config: setup-conda
.PHONY: config

setup-conda: .envs
.PHONY: setup-conda


start: config
	jupyter lab volume_rebalancing.ipynb



.envs:
	conda create --prefix ./envs
	conda install ipykernel jupyter numpy pandas matplotlib seaborn

