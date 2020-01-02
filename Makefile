# how to package python projects: https://packaging.python.org/tutorials/packaging-projects/

clear_dist_dir:
	rm -r dist/*

build_dist: clear_dist_dir
	python3 setup.py sdist bdist_wheel

deploy_to_test_pypi: build_dist
	python3 -m twine upload --repository-url https://test.pypi.org/legacy/ dist/*

deploy_to_pypi: build_dist
	python3 -m twine upload dist/*
