# A RESTful API testing framework example

## Features:
* Support both functional and performance tests

* Common get/post function to 

1. Print every request and response in a API output file
2. Append common headers
3. Take care of request exception and non-200 response codes and return None, so you only need to care normal json response.
        
* Use flask to mock service

* html report
    
## Install:

pip install -U pytest requests Flask pytest-html

## Run:
cd Scripts

**Run Functional tests:**

pytest

**Run Performance tests:**

python perf_test_rest_api.py 
