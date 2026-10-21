.PHONY: fmt fmt-check terraform-validate helm-check python-check demo

fmt:
	terraform -chdir=terraform fmt -recursive

fmt-check:
	terraform -chdir=terraform fmt -check -recursive

terraform-validate:
	terraform -chdir=terraform init -backend=false -input=false
	terraform -chdir=terraform validate

helm-check:
	helm lint helm/platformkit
	helm template platformkit helm/platformkit >/dev/null

python-check:
	python -m compileall -q demo tests demo.py
	python -m unittest discover -s tests -v

demo:
	python demo.py
