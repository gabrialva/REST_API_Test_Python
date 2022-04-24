"""get input test case lists for parametrized tests"""
import os
from os import path
# root_path is parent folder of Scripts folder
# root_path = path.dirname(path.dirname(path.realpath(__file__)))
root_path = path.dirname(path.dirname(path.dirname(path.realpath(__file__)))) # if inside code_snippets subfolder
test_case_list = []
input_root = path.join(root_path, "inputs")
for tc in os.listdir(input_root):
    if tc.startswith("test_case"):
        test_case_list.append(tc)

def parse_ignore_file(file):
    """Parse ignore file and return a list of ignored keys"""
    from os import path
    ignore_keys = []
    if path.isfile(file):
        with open(file) as f:
            for line in f:
                if line.strip != "":
                    ignore_keys.append(line.strip())
    return ignore_keys

def parse_test_input(filename):
    """Parse request test input
    """
    import re
    with open(filename, "r") as f:
        content = f.read()
        # 3 parts split by empty line
        parts = re.split("\n\n", content)
        parts_len = len(parts)

        # part 1: Method and url
        assert len(parts[0].split()) == 2
        method, url = parts[0].split()
        method, url = method.strip(), url.strip()

        # part 2: headers
        if parts_len > 1 and parts[1].strip() != "":
            header_lines = re.split("\s*\n", parts[1])
            header_lines = [line.strip() for line in header_lines]  # strip line spaces
            headers = dict([re.split(":\s*", line) for line in header_lines])
        else:
            headers = {}

        # part 3: body
        if parts_len > 2 and parts[2].strip() != "":
            body = parts[2].strip().strip("\n")
        else:
            body = None

    return method, url, headers, body

def ini_to_dict(input):
    """Covert a ini file to a simple dict
    """
    with open(input) as f:
        content = f.read()
    ret_dict = {}
    for line in content.split("\n"):
        if " = " in line:
            key, value = line.split(" = ", maxsplit=1)
            ret_dict[key] = value
    return ret_dict

def dict_to_ini(dict_var, file=None):
    ini_content_list = []
    def iterate_dict(var, prefix=None):
        """iterate dict and convert to a list of 'key1.key2[i] = value' string"""
        if isinstance(var, dict):
            for k, v in var.items():
                if prefix is None:
                    new_prefix = k  # e.g. age
                else:
                    new_prefix = prefix + "." + k  # e.g. name.firstname
                iterate_dict(v, new_prefix)
        elif isinstance(var, list):
            for index, value in enumerate(var):
                new_prefix = "%s[%d]" % (prefix, index)  # e.g. scores[0]
                iterate_dict(value, new_prefix)
        else:
            # for multiple line string, i.e. with \n, convert to 1 line repr string
            if isinstance(var, str) and "\n" in var:
                var = repr(var)            
            this_item = "%s = %s" % (prefix, var)
            nonlocal ini_content_list
            ini_content_list.append(this_item)

    iterate_dict(dict_var, None)
    ini_content_list.sort()
    ini_content = "\n".join(ini_content_list)
    if file:
        with open(file, "w") as f:
            f.write(ini_content)
    return ini_content

def diff_simple_dict(expected, actual, ignore=[], output_file=None):
    """Compare simple dict generated by ini_to_dict
    """
    diff_list = []
    for key in expected:
        if key not in ignore:
            # missing in actual
            if key not in actual:
                diff_list.append("- %s = %s" % (key, expected[key]))
            # diff
            elif expected[key] != actual[key]:
                diff_list.append("- %s = %s" % (key, expected[key]))
                diff_list.append("+ %s = %s" % (key, actual[key]))

    # more in actual (missing in expected)
    for key in actual:
        if key not in ignore:
            if key not in expected:
                diff_list.append("+ %s = %s" % (key, actual[key]))

    diff_list.sort()
    diff = "\n".join(diff_list)
    if output_file and diff != "":
        with open(output_file, "w") as f:
            f.write(diff)

    return diff

import pytest

@pytest.mark.parametrize("testcase_folder", test_case_list)
def test_by_input_output_text(testcase_folder):
    """test by input and expected output text files"""
    import os
    from os import path
    import requests
    input_root = path.join(root_path, "inputs")
    output_root = path.join(root_path, "outputs")
    expect_root = path.join(root_path, "expects")
    diff_root = path.join(root_path, "diff")
    testcase_full_dir = path.join(input_root, testcase_folder)

    for request_file in os.listdir(testcase_full_dir):
        if not request_file.endswith(".txt"):
            # ignore non-request text files, i.e. .ignore files
            continue

        # parse input files
        request_file_path = path.join(testcase_full_dir, request_file)
        method, url, headers, body = parse_test_input(request_file_path)
        
        resp = requests.request(method, url, headers=headers, data=body, verify=False)
        assert resp.status_code in (200, 201, 202)
        resp = resp.json() # convert to dict

        ## write response dict to ini output
        output_file_dir = path.join(output_root, testcase_folder)
        os.makedirs(output_file_dir, exist_ok=True)
        output_filename = request_file.replace("request_", "response_")
        output_file_path = path.join(output_file_dir, output_filename)
        dict_to_ini(resp, output_file_path)

        # compare
        expect_file_dir = path.join(expect_root, testcase_folder)
        expect_file_path = path.join(expect_file_dir, output_filename)
        ignore_filename = request_file.replace(".txt", ".ignore")
        ignore_file_path = path.join(testcase_full_dir, ignore_filename)
        diff_file_dir = path.join(diff_root, testcase_folder)
        os.makedirs(diff_file_dir, exist_ok=True)
        diff_file_path = path.join(diff_file_dir, output_filename)

        actual = ini_to_dict(output_file_path)
        expected = ini_to_dict(expect_file_path)
        ignore = parse_ignore_file(ignore_file_path)
        diff = diff_simple_dict(actual, expected, ignore=ignore, output_file=diff_file_path)
        assert diff == "", "response does not match expected output"